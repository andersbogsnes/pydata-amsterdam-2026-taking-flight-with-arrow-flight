import io
import pathlib
from collections.abc import Iterator

import pyarrow as pa
import pyarrow.csv
import sqlalchemy as sa
from sqlalchemy.engine.interfaces import DBAPIConnection


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
