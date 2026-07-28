from typing import Iterator

import pyarrow.parquet as pq
from pyarrow import flight
from pyarrow.fs import S3FileSystem, FileSelector, FileInfo


class Server(flight.FlightServerBase):
    def __init__(self, location: str = "grpc://localhost:3000"):
        super().__init__(location=location)
        self._location = location
        self._fs = S3FileSystem(
            access_key="rustfsadmin",
            secret_key="rustfsadmin",
            endpoint_override="http://localhost:9000",
            allow_bucket_creation=True,
            region="eu-north-1",
        )

    def _make_flight_info(self, file: FileInfo) -> flight.FlightInfo:
        metadata = pq.read_metadata(f"events/{file.base_name}", filesystem=self._fs)
        schema = pq.read_schema(f"events/{file.base_name}", filesystem=self._fs)
        descriptor = flight.FlightDescriptor.for_path(file.base_name)
        return flight.FlightInfo(
            schema=schema,
            endpoints=[
                flight.FlightEndpoint(
                    flight.Ticket(file.base_name),
                    locations=[self._location],
                )
            ],
            descriptor=descriptor,
            total_records=metadata.num_rows,
        )

    def get_flight_info(
        self, context: flight.ServerCallContext, descriptor: flight.FlightDescriptor
    ) -> flight.FlightInfo:
        path = descriptor.path[0].decode("utf-8")
        file = self._fs.get_file_info(path)
        return self._make_flight_info(file)

    def list_flights(
        self, context: flight.ServerCallContext, criteria: bytes = None
    ) -> Iterator[flight.FlightInfo]:
        files: list[FileInfo] = self._fs.get_file_info(FileSelector("events"))
        for file in files:
            yield self._make_flight_info(file)

    def do_get(
        self, context: flight.ServerCallContext, ticket: flight.Ticket
    ) -> flight.GeneratorStream:
        path = ticket.ticket.decode("utf-8")
        data = pq.ParquetFile(f"events/{path}", filesystem=self._fs, pre_buffer=True)
        return flight.GeneratorStream(
            schema=data.schema_arrow, generator=data.iter_batches(batch_size=125_000)
        )

    def do_put(
        self,
        context: flight.ServerCallContext,
        descriptor: flight.FlightDescriptor,
        reader: flight.MetadataRecordBatchReader,
        writer: flight.FlightMetadataWriter,
    ) -> None:
        path = f"events/{descriptor.path[0].decode('utf-8')}"

        with self._fs.open_output_stream(path) as f:
            with pq.ParquetWriter(f, reader.schema) as writer:
                for chunk in reader:
                    writer.write_batch(chunk.data)

    @property
    def url(self) -> str:
        return self._location
