import pathlib

import polars as pl
from pyarrow import flight
import pyarrow.csv as pc


class Client:
    def __init__(self, location: str = "grpc://localhost:3000"):
        self._client = flight.FlightClient(location=location)

    def fetch_data(self, dataset: str) -> pl.DataFrame:
        info = self._client.get_flight_info(flight.FlightDescriptor.for_path(dataset))
        reader: flight.FlightStreamReader = self._client.do_get(
            info.endpoints[0].ticket
        )
        return pl.from_arrow(reader.to_reader())

    def upload_data(self, dataset: pathlib.Path):
        upload_path = dataset.with_suffix(".parquet").name
        descriptor = flight.FlightDescriptor.for_path(upload_path)

        writer: flight.FlightStreamWriter

        with pc.open_csv(dataset) as csv_data:
            writer, _ = self._client.do_put(descriptor, csv_data.schema)
            with writer:
                for batch in csv_data:
                    writer.write_batch(batch)
