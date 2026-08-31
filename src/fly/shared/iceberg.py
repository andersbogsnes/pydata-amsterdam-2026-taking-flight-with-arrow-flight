import pathlib

from flight_server.client import Client
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from fly.console import console


def handle_iceberg_upload(
    client: Client,
    table_name: str,
    data_file: pathlib.Path,
    dtypes: dict | None = None,
):
    """Uploads the data file to the Iceberg table"""

    if client.table_exists(table_name):
        console.print(
            f" [green]✔[/green] Iceberg table {table_name} already has records"
            " - skipping"
        )
        return

    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as transfer_progress:
        upload_file_task = transfer_progress.add_task(
            "Uploading messages to Iceberg", total=data_file.stat().st_size
        )

        for count in client.upload_data(
            table_name,
            data_file,
            dtypes,
            metadata={"description": "NYC CitiBike trips"},
            with_progress=True,
        ):
            transfer_progress.update(
                upload_file_task,
                completed=count,
            )
        transfer_progress.update(
            upload_file_task,
            description=" [green]✔[/green] Upload to Iceberg complete!",
        )
