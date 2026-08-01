import pathlib

import pyarrow as pa
from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn, \
    TimeRemainingColumn

from flight_server.client import Client
from fly.console import console


def _upload_messages_to_iceberg(
        client: Client, local_file_path: pathlib.Path, table_name: str, dtypes: dict | None
) -> None:
    """Inner batched upload - performs the upload in batches.
    Yields the byte progress, so the progress bar can update
    """
    # Open the file directly to get access to `.tell` to keep track of read bytes


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
            "Uploading messages to Iceberg", total=1
        )
        client.upload_data(table_name, data_file, dtypes={
            "platform": "string",
            "category": "string",
            "created_at": pa.timestamp("us"),
            "blocked_at": pa.timestamp("us"),
            "updated_at": pa.timestamp("us")
        })

        transfer_progress.update(
            upload_file_task,
            completed=1,
            description="[green]✔[/green] Upload to Iceberg complete!"
        )
