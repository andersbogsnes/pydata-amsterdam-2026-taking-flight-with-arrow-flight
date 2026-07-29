import pathlib
from typing import Annotated

import cyclopts
import sqlalchemy as sa
from pyarrow.fs import S3FileSystem
from pyiceberg.catalog.rest import RestCatalog
from pyiceberg.exceptions import NamespaceAlreadyExistsError
from pyiceberg.typedef import Identifier
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from taking_flight.cli.bootstrap.catalog import _bootstrap_catalog
from taking_flight.cli.bootstrap.db import _upload_message_to_db
from taking_flight.cli.bootstrap.iceberg import _upload_messages_to_iceberg
from taking_flight.cli.bootstrap.services import (
    _create_bucket,
    _start_compose,
    _stop_compose,
)
from taking_flight.cli.console import console
from taking_flight.rest import db as rest_db
from taking_flight.settings import Settings

app = cyclopts.App(
    name="bootstrap", help="Start backing services and upload initial data"
)

DATA_DIR = pathlib.Path(__file__).parents[4] / "data"
MESSAGES_URL = "https://www.kaggle.com/datasets/mkechinov/direct-messaging?select=messages-demo.csv"
CAMPAIGNS_URL = (
    "https://www.kaggle.com/datasets/mkechinov/direct-messaging?select=campaigns.csv"
)
MESSAGES_FILE = DATA_DIR / "messages-demo.csv"
CAMPAIGNS_FILE = DATA_DIR / "campaigns.csv"
NAMESPACE = "events"

transfer_progress = Progress(
    "[progress.description]{task.description}",
    BarColumn(),
    DownloadColumn(),
    TransferSpeedColumn(),
    TimeRemainingColumn(),
    console=console,
)


def _handle_iceberg_upload(
        catalog: RestCatalog, identifier: Identifier, data_file: pathlib.Path
):
    """Uploads the data file to the Iceberg table - wraps the inner upload loop with
    progress bars
    """
    if catalog.table_exists(identifier):
        console.print(
            f"[green]✓[/green] ️Already uploaded {data_file.name} to {'.'.join(identifier)}"
            " - skipping"
        )
        return

    try:
        catalog.create_namespace(identifier[0])
    except NamespaceAlreadyExistsError:
        pass

    with transfer_progress:
        upload_file_task = transfer_progress.add_task(
            "Uploading messages to Iceberg", total=data_file.stat().st_size
        )
        for completed_bytes in _upload_messages_to_iceberg(
                catalog, data_file, identifier
        ):
            transfer_progress.update(upload_file_task, completed=completed_bytes)
        transfer_progress.update(
            upload_file_task, description="[green]✓[/green] Upload to Iceberg complete!"
        )
    transfer_progress.remove_task(upload_file_task)


def _handle_db_upload(engine: sa.Engine, db_table: sa.Table, data_file: pathlib.Path):
    """Uploads the data file to the DB table - wraps the inner upload loop with progress bars"""
    with engine.begin() as conn:
        sql = sa.select(sa.func.count(db_table.c.id))
        row_count = conn.execute(sql).scalar_one()
        if row_count > 0:
            console.print(
                f"[green]✓[/green] DB {db_table.name} already has records - skipping"
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


@app.command()
def up(
        namespace: str = NAMESPACE,
        services: Annotated[bool, cyclopts.Parameter(help="Start backing services")] = True,
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

    settings = Settings()
    s3_fs = S3FileSystem(
        access_key=settings.s3_access_key.get_secret_value(),
        secret_key=settings.s3_secret_key.get_secret_value(),
        endpoint_override=settings.s3_url,
        allow_bucket_creation=True,
        region=settings.s3_region,
    )

    engine = sa.create_engine(settings.db_url.unicode_string())

    if services:
        _start_compose()
    _create_bucket(s3_fs, settings.bucket_name)
    _bootstrap_catalog(settings)
    rest_db.meta.create_all(engine)
    catalog = RestCatalog(
        "default", uri=f"{settings.catalog_url}/catalog", warehouse="default"
    )
    _handle_iceberg_upload(catalog, (namespace, "messages"), MESSAGES_FILE)
    _handle_db_upload(engine, rest_db.messages_table, MESSAGES_FILE)
    console.print("🔗 Notebook is ready! http://localhost:8080")


@app.command()
def down(remove_volumes: bool = True):
    """Shut down backing services"""
    _stop_compose(remove_volumes=remove_volumes)
