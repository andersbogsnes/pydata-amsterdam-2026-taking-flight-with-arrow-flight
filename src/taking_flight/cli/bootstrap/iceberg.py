import pathlib
from collections.abc import Iterator

import pyarrow as pa
import pyarrow.csv
from pyiceberg.catalog.rest import RestCatalog
from pyiceberg.typedef import Identifier


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
