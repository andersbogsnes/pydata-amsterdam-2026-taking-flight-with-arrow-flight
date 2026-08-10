import io
import pathlib
from collections.abc import Iterator

import pyarrow.csv
import sqlalchemy as sa
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from sqlalchemy.engine.interfaces import DBAPIConnection

from fly.console import console


def _upload_message_to_db(
    engine: sa.Engine, table_name: str, local_file_path: pathlib.Path
) -> Iterator[int]:
    """Inner loop to handle COPY INTO the Postgres database"""
    with local_file_path.open("rb") as f, engine.begin() as conn:
        raw_conn: DBAPIConnection | None = conn.connection.dbapi_connection
        if raw_conn is None:
            raise RuntimeError("Connection not open")
        with (
            pyarrow.csv.open_csv(f) as reader,
            raw_conn.cursor() as cursor,  # type: ignore
            cursor.copy(f"COPY {table_name} (ride_id, rideable_type, started_at, ended_at, start_station_name, start_station_id, end_station_name, end_station_id, start_lat, start_lng, end_lat, end_lng, member_casual) FROM STDIN (FORMAT CSV)") as copy,
        ):
            write_options = pyarrow.csv.WriteOptions(include_header=False)
            for batch in reader:
                buf = io.BytesIO()
                pyarrow.csv.write_csv(batch, buf, write_options=write_options)
                copy.write(buf.getvalue())
                yield f.tell()


def handle_db_upload(engine: sa.Engine, db_table: sa.Table, data_file: pathlib.Path):
    """Uploads the data file to the DB table - wraps the inner upload loop with progress bars"""
    with engine.begin() as conn:
        sql = sa.select(sa.func.count()).select_from(db_table)
        row_count = conn.execute(sql).scalar_one()
        if row_count > 0:
            console.print(
                f" [green]✔[/green] Database table {db_table.name} already has records - skipping"
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
        upload_task = transfer_progress.add_task(
            "Uploading messages to DB", total=data_file.stat().st_size
        )
        for completed_bytes in _upload_message_to_db(engine, db_table.name, data_file):
            transfer_progress.update(upload_task, completed=completed_bytes)

        transfer_progress.update(
            upload_task, description=" [green]✔[/green] Upload to db complete!"
        )
    transfer_progress.remove_task(upload_task)
