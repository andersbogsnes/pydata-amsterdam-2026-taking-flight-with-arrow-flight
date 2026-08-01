import pathlib

import polars as pl
import pyarrow.csv
from pyarrow import flight


class Client:
    def __init__(self, location: str = "grpc://localhost:7000"):
        self._client = flight.FlightClient(location=location)

    def fetch_data(self, table: str) -> pl.DataFrame:
        info = self._client.get_flight_info(flight.FlightDescriptor.for_path(table))
        reader: flight.FlightStreamReader = self._client.do_get(
            info.endpoints[0].ticket
        )
        return pl.DataFrame(reader.to_reader())

    def upload_data(self, table: str, data: pathlib.Path, dtypes: dict | None = None) -> str:
        descriptor = flight.FlightDescriptor.for_path(table)
        writer: flight.FlightStreamWriter
        reader: flight.FlightMetadataReader

        if dtypes is None:
            convert_options = None
        else:
            convert_options = pyarrow.csv.ConvertOptions(
                true_values=["t"],
                false_values=["f"],
                column_types=dtypes)

        with data.open("rb") as f:
            csv_reader = pyarrow.csv.open_csv(f, convert_options=convert_options)
            writer, reader = self._client.do_put(descriptor, csv_reader.schema)

            for batch in csv_reader:
                writer.write_batch(batch)
            writer.done_writing()

        # Get the byte representation from the server
        msg = reader.read()

        return msg.decode()
