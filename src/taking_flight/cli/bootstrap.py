import io
import pathlib
import subprocess
from typing import Iterator, Annotated

import cyclopts
import pyarrow as pa
import pyarrow.csv
import sqlalchemy as sa
from cyclopts import Parameter
from pyarrow import parquet as pq
from pyarrow.fs import FileSystem, FileType, S3FileSystem
from python_on_whales import DockerClient
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from sqlalchemy.engine.interfaces import DBAPIConnection

from taking_flight.cli.console import console
from taking_flight.flight_server import db as flight_db
from taking_flight.flight_server.db import dataset_table
from taking_flight.rest import db as rest_db
from taking_flight.rest.settings import Settings

app = cyclopts.App(
    name="bootstrap", help="Start backing services and upload initial data"
)
settings = Settings()
s3_fs = S3FileSystem(
    access_key=settings.access_key.get_secret_value(),
    secret_key=settings.secret_key.get_secret_value(),
    endpoint_override=settings.s3_endpoint.unicode_string(),
    allow_bucket_creation=True,
    region=settings.region,
)

DATA_DIR = pathlib.Path(__file__).parents[3] / "data"
MESSAGES_URL = "https://www.kaggle.com/datasets/mkechinov/direct-messaging?select=messages-demo.csv"
CAMPAIGNS_URL = (
    "https://www.kaggle.com/datasets/mkechinov/direct-messaging?select=campaigns.csv"
)
MESSAGES_FILE = DATA_DIR / "messages-demo.csv"
CAMPAIGNS_FILE = DATA_DIR / "campaigns.csv"
BUCKET_NAME = "events"
DB_URL = Settings().db_url.unicode_string()

transfer_progress = Progress(
    "[progress.description]{task.description}",
    BarColumn(),
    DownloadColumn(),
    TransferSpeedColumn(),
    TimeRemainingColumn(),
    console=console,
)

status_progress = Progress(
    SpinnerColumn(finished_text="[green]✓[/green]"),
    "{task.description}",
    console=console,
)


def _start_compose(services: list[str] | None = None) -> None:
    docker = DockerClient()
    docker.compose.up(
        detach=True,
        quiet=True,
        services=services,
        wait=True,
        build=True,
    )


def _stop_compose(remove_volumes: bool = True) -> None:
    docker = DockerClient()
    docker.compose.down(quiet=True, remove_orphans=True, volumes=remove_volumes, timeout=10)


def _create_bucket(fs: FileSystem, bucket_name: str) -> None:
    fs.create_dir(bucket_name)


def _upload_message_to_db(
    engine: sa.Engine, local_file_path: pathlib.Path
) -> Iterator[int]:
    with local_file_path.open("rb") as f, engine.begin() as conn:
        raw_conn: DBAPIConnection | None = conn.connection.dbapi_connection
        if raw_conn is None:
            raise RuntimeError("Connection not open")
        with pyarrow.csv.open_csv(
            f,
            convert_options=pyarrow.csv.ConvertOptions(
                true_values=["t"],
                false_values=["f"],
                column_types={"platform": "string", "blocked_at": pa.timestamp("s")},
            ),
        ) as reader:
            with (
                raw_conn.cursor() as cursor,  # ty:ignore[invalid-context-manager]
                cursor.copy("COPY messages FROM STDIN (FORMAT CSV)") as copy,
            ):
                write_options = pyarrow.csv.WriteOptions(include_header=False)
                for batch in reader:
                    buf = io.BytesIO()
                    pyarrow.csv.write_csv(batch, buf, write_options=write_options)
                    copy.write(buf.getvalue())
                    yield f.tell()


def _upload_messages_to_bucket(
    fs: FileSystem, local_file_path: pathlib.Path, bucket_name: str
) -> Iterator[int]:
    # Open the file directly to get access to `.tell` to keep track of read bytes
    with local_file_path.open("rb") as f:
        with pyarrow.csv.open_csv(
            f,
            convert_options=pyarrow.csv.ConvertOptions(
                true_values=["t"],
                false_values=["f"],
                column_types={"platform": "string", "blocked_at": pa.timestamp("s")},
            ),
        ) as reader:
            writer = pq.ParquetWriter(
                f"{bucket_name}/messages.parquet",
                reader.schema,
                filesystem=fs,
            )
            try:
                for chunk in reader:
                    writer.write_batch(chunk)
                    yield f.tell()
            finally:
                writer.close()


def _handle_bucket_upload(
    engine: sa.Engine, bucket_name: str, messages_file: pathlib.Path
):
    _create_bucket(s3_fs, bucket_name)

    if s3_fs.get_file_info(f"{bucket_name}/messages.parquet").type != FileType.NotFound:
        console.print(
            f"[green]✓[/green] ️Already uploaded messages.parquet to {bucket_name} "
            "- skipping"
        )
        return
    with transfer_progress:
        upload_file_task = transfer_progress.add_task(
            "Uploading messages to bucket", total=messages_file.stat().st_size
        )
        for completed_bytes in _upload_messages_to_bucket(
            s3_fs, messages_file, bucket_name
        ):
            transfer_progress.update(upload_file_task, completed=completed_bytes)
        transfer_progress.update(
            upload_file_task, description="[green]✓[/green] Upload to bucket complete!"
        )
        result = pq.read_metadata(f"{bucket_name}/messages.parquet", filesystem=s3_fs)
        size = s3_fs.get_file_info(f"{bucket_name}/messages.parquet").size

        with engine.begin() as conn:
            sql = dataset_table.insert().values(
                name="messages",
                bucket=bucket_name,
                file_name="messages.parquet",
                file_type="parquet",
                num_partitions=result.num_row_groups,
                num_rows=result.num_rows,
                serialized_size=size,
                description="Contains a list of all messages sent with its statuses and meta info.",
            )
            conn.execute(sql)
    transfer_progress.remove_task(upload_file_task)


def _handle_db_upload(engine: sa.Engine, messages_file: pathlib.Path):
    with engine.begin() as conn:
        sql = sa.select(sa.func.count(rest_db.messages_table.c.id))
        row_count = conn.execute(sql).scalar_one()
        if row_count > 0:
            console.print("[green]✓[/green] DB already has messages - skipping")
            return

    with transfer_progress:
        upload_task = transfer_progress.add_task(
            "Uploading messages to DB", total=messages_file.stat().st_size
        )
        for completed_bytes in _upload_message_to_db(engine, messages_file):
            transfer_progress.update(upload_task, completed=completed_bytes)

        transfer_progress.update(
            upload_task, description="[green]✓[/green] Upload to db complete!"
        )
    transfer_progress.remove_task(upload_task)


def _start_notebook():
    subprocess.run(["jupyter", "lab", "--notebook-dir", "notebooks"])


@app.command()
def up(
    bucket_name: str = BUCKET_NAME,
    db_url: str = DB_URL,
):
    """Start backing services and upload initial data"""
    for data_file in [MESSAGES_FILE, CAMPAIGNS_FILE]:
        if not data_file.exists():
            console.print(
                f"❌ [red]{data_file} doesn't exist. "
                f"Go to {data_file}, download and extract it to the data folder"
            )
            return
    engine = sa.create_engine(db_url)
    services = ["db", "storage", "rest", "server", "notebook"]
    with status_progress:
        for service in services:
            task = status_progress.add_task(f"Starting {service.title()}", total=1)
            _start_compose([service])
            status_progress.update(
                task, description=f"{service.title()} started!", advance=1
            )
        rest_db.meta.create_all(engine)
        flight_db.meta.create_all(engine)
        _handle_bucket_upload(engine, bucket_name, MESSAGES_FILE)
        _handle_db_upload(engine, MESSAGES_FILE)
    console.print("🔗 Notebook is ready! http://localhost:8080")


@app.command()
def down(remove_volumes: bool = True):
    """Shut down backing services"""
    with status_progress:
        task = status_progress.add_task("Shutting down backing services...", total=1)
        _stop_compose(remove_volumes=remove_volumes)
        status_progress.update(
            task, description="Backing services stopped!", completed=1
        )
