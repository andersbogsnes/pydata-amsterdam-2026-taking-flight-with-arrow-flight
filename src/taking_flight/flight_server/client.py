import pathlib

import polars as pl
from pyarrow import flight
from pyarrow.csv import read_csv


class Client:
    def __init__(self, location: str = "grpc://localhost:7000"):
        self._client = flight.FlightClient(location=location)

    def fetch_data(self, dataset: str) -> pl.DataFrame:
        info = self._client.get_flight_info(flight.FlightDescriptor.for_path(dataset))
        reader: flight.FlightStreamReader = self._client.do_get(
            info.endpoints[0].ticket
        )
        return pl.DataFrame(reader.to_reader())

    def upload_data(self, data: pathlib.Path) -> int:
        upload_path = data.with_suffix(".parquet").name
        descriptor = flight.FlightDescriptor.for_path(upload_path)
        data = read_csv(data)

        writer: flight.FlightStreamWriter
        reader: flight.FlightMetadataReader

        writer, reader = self._client.do_put(descriptor, data.schema)
        writer.write_table(data)
        writer.done_writing()

        # Get the byte representation from the server
        num_rows = reader.read()

        return int.from_bytes(num_rows)
