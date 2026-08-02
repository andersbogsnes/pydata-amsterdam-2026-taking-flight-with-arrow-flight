import pathlib

import pyarrow as pa
from flight_server.client import Client
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from fly.console import console


def _handle_iceberg_upload(
    client: Client, namespace_name: str, table_name: str, data_file: pathlib.Path
):
    """Uploads the data file to the Iceberg table - wraps the inner upload loop with
    progress bars
    """

    client.create_namespace(namespace_name)

    if client.table_exists(table_name):
        console.print(
            f"[green]✔[/green] ️Already uploaded {data_file.stem} to {table_name}"
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
            dtypes={
                "platform": "string",
                "category": "string",
                "created_at": pa.timestamp("us"),
                "blocked_at": pa.timestamp("us"),
                "updated_at": pa.timestamp("us"),
            },
            with_progress=True,
        ):
            transfer_progress.update(
                upload_file_task,
                completed=count,
            )
        transfer_progress.update(
            upload_file_task, description="[green]✔[/green] Upload to Iceberg complete!"
        )
