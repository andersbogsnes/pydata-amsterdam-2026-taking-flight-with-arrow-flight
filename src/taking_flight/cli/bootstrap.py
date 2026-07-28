import io
import pathlib
import subprocess
from collections.abc import Iterator

import cyclopts
import httpx2
import pyarrow as pa
import pyarrow.csv
import sqlalchemy as sa
from pyarrow.fs import FileSystem, S3FileSystem
from pyiceberg.catalog.rest import RestCatalog
from pyiceberg.exceptions import NamespaceAlreadyExistsError
from pyiceberg.typedef import Identifier
from python_on_whales import DockerClient
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from sqlalchemy.engine.interfaces import DBAPIConnection

from taking_flight.cli.console import console
from taking_flight.rest import db as rest_db
from taking_flight.settings import Settings

app = cyclopts.App(
    name="bootstrap", help="Start backing services and upload initial data"
)
settings = Settings()
s3_fs = S3FileSystem(
    access_key=settings.s3_access_key.get_secret_value(),
    secret_key=settings.s3_secret_key.get_secret_value(),
    endpoint_override=settings.s3_url,
    allow_bucket_creation=True,
    region=settings.s3_region,
)

DATA_DIR = pathlib.Path(__file__).parents[3] / "data"
MESSAGES_URL = "https://www.kaggle.com/datasets/mkechinov/direct-messaging?select=messages-demo.csv"
CAMPAIGNS_URL = (
    "https://www.kaggle.com/datasets/mkechinov/direct-messaging?select=campaigns.csv"
)
MESSAGES_FILE = DATA_DIR / "messages-demo.csv"
CAMPAIGNS_FILE = DATA_DIR / "campaigns.csv"
NAMESPACE = "events"
DB_URL = settings.db_url.unicode_string()
CATALOG_URL = settings.catalog_url

transfer_progress = Progress(
    "[progress.description]{task.description}",
    BarColumn(),
    DownloadColumn(),
    TransferSpeedColumn(),
    TimeRemainingColumn(),
    console=console,
)


def _start_compose() -> None:
    docker = DockerClient()
    docker.compose.up(
        detach=True,
        build=True,
    )


def _stop_compose(remove_volumes: bool = True) -> None:
    docker = DockerClient()
    docker.compose.down(remove_orphans=True, volumes=remove_volumes, timeout=10)


def _create_bucket(fs: FileSystem, bucket_name: str) -> None:
    fs.create_dir(bucket_name)


def _bootstrap_catalog(catalog_url: str) -> None:
    resp = httpx2.post(
        f"{catalog_url}/management/v1/bootstrap", json={"accept-terms-of-use": True}
    )

    match resp.status_code:
        case 201:
            console.print("[green]✔[/green] Catalog bootstrapped successfully")
        case 204:
            console.print("[green]✔[/green] Catalog already bootstrapped")
        case 400:
            message = resp.json()
            if message.get("error", {}).get("type") == "CatalogAlreadyBootstrapped":
                console.print("[green]✔[/green] Catalog already bootstrapped")
            else:
                console.print(message)
                raise RuntimeError("Failed to bootstrap catalog")
        case _:
            console.print(resp.text)
            raise RuntimeError("Failed to bootstrap catalog")

    resp = httpx2.post(
        f"{catalog_url}/management/v1/warehouse",
        json={
            "warehouse-name": "default",
            "default-format-version": 3,
            "storage-profile": {
                "type": "s3",
                "bucket": settings.bucket_name,
                "key-prefix": "iceberg",
                "path-style-access": True,
                "endpoint": settings.s3_catalog_endpoint,
                "region": settings.s3_region,
                "flavor": "s3-compat",
                "sts-enabled": True,
                "sts-endpoint": settings.s3_catalog_endpoint,
                "remote-signing-enabled": False,
            },
            "storage-credential": {
                "type": "s3",
                "credential-type": "access-key",
                "aws-access-key-id": settings.s3_access_key.get_secret_value(),
                "aws-secret-access-key": settings.s3_secret_key.get_secret_value(),
            },
            "delete-profile": {
                "type": "hard",
            },
        },
    )

    match resp.status_code:
        case 201:
            console.print("[green]✔[/green] Warehouse bootstrapped successfully")
        case 204:
            console.print("[green]✔[/green] Warehouse already bootstrapped")
        case 400:
            message = resp.json()
            match message.get("error", {}).get("type"):
                case "CreateWarehouseStorageProfileOverlap":
                    console.print("[green]✔[/green] Warehouse already bootstrapped")
                case _:
                    console.print(message)
                    raise RuntimeError(f"Failed to bootstrap warehouse: {message}")
        case _:
            console.print(resp.text)
            raise RuntimeError(f"Failed to bootstrap catalog: {resp.text}")


def _upload_message_to_db(
    engine: sa.Engine, table_name: str, local_file_path: pathlib.Path
) -> Iterator[int]:
    """Inner loop to handle COPY INTO the Postgres database"""
    with local_file_path.open("rb") as f, engine.begin() as conn:
        raw_conn: DBAPIConnection | None = conn.connection.dbapi_connection
        if raw_conn is None:
            raise RuntimeError("Connection not open")
        with (
            pyarrow.csv.open_csv(
                f,
                convert_options=pyarrow.csv.ConvertOptions(
                    true_values=["t"],
                    false_values=["f"],
                    column_types={
                        "platform": "string",
                        "blocked_at": pa.timestamp("s"),
                    },
                ),
            ) as reader,
            raw_conn.cursor() as cursor,
            cursor.copy(f"COPY {table_name} FROM STDIN (FORMAT CSV)") as copy,
        ):
            write_options = pyarrow.csv.WriteOptions(include_header=False)
            for batch in reader:
                buf = io.BytesIO()
                pyarrow.csv.write_csv(batch, buf, write_options=write_options)
                copy.write(buf.getvalue())
                yield f.tell()


def _upload_messages_to_iceberg(
    catalog: RestCatalog, local_file_path: pathlib.Path, identifier: Identifier
) -> Iterator[int]:
    """Inner batched upload - performs the upload in batches. Yields the byte progress, so the progress
    bar can update
    """
    # Open the file directly to get access to `.tell` to keep track of read bytes
    with (
        local_file_path.open("rb") as f,
        pyarrow.csv.open_csv(
            f,
            convert_options=pyarrow.csv.ConvertOptions(
                true_values=["t"],
                false_values=["f"],
                column_types={
                    "platform": "string",
                    "category": "string",
                    "created_at": pa.timestamp("us"),
                    "updated_at": pa.timestamp("us"),
                    "blocked_at": pa.timestamp("s"),
                },
            ),
        ) as reader,
    ):
        table = catalog.create_table(identifier, reader.schema)
        with table.transaction() as tx:
            for chunk in reader:
                tx.append([chunk.data])
                yield f.tell()


def _handle_iceberg_upload(
    catalog: RestCatalog, identifier: Identifier, data_file: pathlib.Path
):
    """Uploads the data file to the Iceberg table - wraps the inner upload loop with
    progress bars
    """
    if catalog.table_exists(identifier):
        console.print(
            f"[green]✓[/green] ️Already uploaded {data_file.name} to {identifier}"
            "- skipping"
        )
        return

    try:
        catalog.create_namespace(identifier[0])
    except NamespaceAlreadyExistsError:
        pass

    with transfer_progress:
        upload_file_task = transfer_progress.add_task(
            "Uploading messages to bucket", total=data_file.stat().st_size
        )
        for completed_bytes in _upload_messages_to_iceberg(
            catalog, data_file, identifier
        ):
            transfer_progress.update(upload_file_task, completed=completed_bytes)
        transfer_progress.update(
            upload_file_task, description="[green]✓[/green] Upload to bucket complete!"
        )
    transfer_progress.remove_task(upload_file_task)


def _handle_db_upload(engine: sa.Engine, db_table: sa.Table, data_file: pathlib.Path):
    """Uploads the data file to the DB table - wraps the inner upload loop with progress bars"""
    with engine.begin() as conn:
        sql = sa.select(sa.func.count(db_table.c.id))
        row_count = conn.execute(sql).scalar_one()
        if row_count > 0:
            console.print(
                f"[green]✓[/green] DB {db_table.name} already has  - skipping"
            )
            return

    with transfer_progress:
        upload_task = transfer_progress.add_task(
            "Uploading messages to DB", total=data_file.stat().st_size
        )
        for completed_bytes in _upload_message_to_db(engine, db_table.name, data_file):
            transfer_progress.update(upload_task, completed=completed_bytes)

        transfer_progress.update(
            upload_task, description="[green]✓[/green] Upload to db complete!"
        )
    transfer_progress.remove_task(upload_task)


def _start_notebook():
    try:
        subprocess.run(["jupyter", "lab", "--notebook-dir", "notebooks"], check=True)
    except subprocess.CalledProcessError as e:
        console.print("Failed to start JupyterLab")
        console.print(e.output)
        raise


@app.command()
def up(
    namespace: str = NAMESPACE,
    db_url: str = DB_URL,
):
    """Start backing services and upload initial data"""
    for location, data_file in zip(
        [MESSAGES_URL, CAMPAIGNS_URL], [MESSAGES_FILE, CAMPAIGNS_FILE]
    ):
        if not data_file.exists():
            console.print(
                f"❌ [red]{data_file} doesn't exist. "
                f"Go to {location}, download and extract it to the data folder"
            )
            return
    engine = sa.create_engine(db_url)

    _start_compose()
    _create_bucket(s3_fs, settings.bucket_name)
    _bootstrap_catalog(CATALOG_URL)
    rest_db.meta.create_all(engine)
    catalog = RestCatalog(
        "default", uri="http://localhost:8181/catalog", warehouse="default"
    )
    _handle_iceberg_upload(catalog, (NAMESPACE, "messages"), MESSAGES_FILE)
    _handle_db_upload(engine, rest_db.messages_table, MESSAGES_FILE)
    console.print("🔗 Notebook is ready! http://localhost:8080")


@app.command()
def down(remove_volumes: bool = True):
    """Shut down backing services"""
    _stop_compose(remove_volumes=remove_volumes)
