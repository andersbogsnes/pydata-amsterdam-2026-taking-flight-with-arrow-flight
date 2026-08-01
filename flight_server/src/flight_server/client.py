import pathlib
from typing import Self

import attrs
import polars as pl
import pyarrow.csv
from pyarrow import flight
import pyarrow as pa
from flight_server.models import CreateNamespaceRequest


@attrs.define
class Client:
    _client: flight.FlightClient

    @classmethod
    def for_location(cls, location: str = "grpc://localhost:7000") -> Self:
        client = flight.FlightClient(location)
        return cls(client=client)

    def ping(self):
        return self._client.wait_for_available()

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
            convert_options = pyarrow.csv.ConvertOptions(
                true_values=["t"],
                false_values=["f"],
            )
        else:
            convert_options = pyarrow.csv.ConvertOptions(
                true_values=["t"],
                false_values=["f"],
                column_types=dtypes)

        with data.open("rb") as f:
            csv_reader = pyarrow.csv.open_csv(f, convert_options=convert_options,
                                              )
            writer, reader = self._client.do_put(descriptor, csv_reader.schema)

            for batch in csv_reader:
                writer.write_batch(batch)
            writer.done_writing()

        # Get the byte representation from the server
        msg: pa.Buffer = reader.read()

        return msg.to_pybytes().decode()

    def table_exists(self, table: str) -> bool:
        try:
            info: flight.FlightInfo = self._client.get_flight_info(
                flight.FlightDescriptor.for_path(table))
        except flight.FlightServerError:
            return False

        if info.total_records <= 0:
            return False

        return True

    def create_namespace(self, name: str) -> None:
        request = CreateNamespaceRequest(name=name)
        self._client.do_action(flight.Action(action_type="create_namespace",
                                             buf=request.model_dump_json().encode()
                                             ))
