import pathlib
from collections.abc import Iterator
from typing import Literal, Self, overload

import attrs
import polars as pl
import pyarrow.csv
from pyarrow import flight

from flight_server import models
from flight_server.models import CreateNamespaceRequest


@attrs.define
class Client:
    _client: flight.FlightClient

    @classmethod
    def for_location(cls, location: str = "grpc://localhost:7000") -> Self:
        client = flight.FlightClient(location)
        return cls(client=client)

    def ping(self, timeout=5) -> None:
        """Waits until the server is up and running.
        Parameters
        ----------
        timeout: int
            How long in seconds to wait
        """
        return self._client.wait_for_available(timeout=timeout)

    def fetch_data(self, table: str) -> pl.DataFrame:
        """Fetches the data from the given table.

        Parameters
        ----------
        table: str
            The table to fetch the data from.

        Returns
        -------
        pl.DataFrame
            The data in the form of a polars table
        """
        info = self._client.get_flight_info(flight.FlightDescriptor.for_path(table))
        reader: flight.FlightStreamReader = self._client.do_get(
            info.endpoints[0].ticket
        )
        return pl.DataFrame(reader.to_reader())

    @overload
    def upload_data(
        self,
        table: str,
        data: pathlib.Path,
        dtypes: dict | None = None,
        metadata: dict | None = None,
        with_progress: Literal[True] = True,
    ) -> Iterator[int]: ...

    @overload
    def upload_data(
        self,
        table: str,
        data: pathlib.Path,
        dtypes: dict | None = None,
        metadata: dict | None = None,
        with_progress: Literal[False] = False,
    ) -> models.DoPutResponse: ...

    def upload_data(
        self,
        table: str,
        data: pathlib.Path,
        dtypes: dict | None = None,
        metadata: dict | None = None,
        with_progress: bool = False,
    ) -> Iterator[int] | models.DoPutResponse:
        """Upload the data file to the given table.

        Parameters
        ----------
        table: str
            The tablename to upload the data to.
        data: pathlib.Path
            The path to the CSV file to upload.
        dtypes: dict
            Mapping of column names to dtypes. Passed to pyarrow.csv.ConvertOptions.
        metadata: dict
            Mapping of metadata to include on the table
        with_progress: bool
            If true, return an iterator of bytes read. Used for progress bars
        """
        if data.suffix != ".csv":
            raise NotImplementedError("unable to upload csv")

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
                true_values=["t"], false_values=["f"], column_types=dtypes
            )

        with data.open("rb") as f:
            csv_reader = pyarrow.csv.open_csv(
                f,
                convert_options=convert_options,
            )
            schema = csv_reader.schema

            if metadata is not None:
                schema = csv_reader.schema.with_metadata(
                    metadata,
                )
            writer, reader = self._client.do_put(descriptor, schema)

            for batch in csv_reader:
                writer.write(batch)
                if with_progress:
                    yield f.tell()

            writer.done_writing()

            if not with_progress:
                msg = reader.read()
                return models.DoPutResponse.model_validate_json(
                    msg.to_pybytes().decode()
                )
            return f.tell()

    def table_exists(self, table: str) -> bool:
        try:
            info: flight.FlightInfo = self._client.get_flight_info(
                flight.FlightDescriptor.for_path(table)
            )
        except flight.FlightServerError:
            return False

        return info.total_records >= 0

    def create_namespace(self, name: str) -> None:
        request = CreateNamespaceRequest(name=name)
        self._client.do_action(
            flight.Action(
                action_type="create_namespace", buf=request.model_dump_json().encode()
            )
        )
