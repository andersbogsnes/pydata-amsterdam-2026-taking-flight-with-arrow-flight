from typing import Literal
from typing import Self

from pydantic import BaseModel, ConfigDict


class DeleteDatasetRequest(BaseModel):
    name: str


class UpdateDatasetRequest(BaseModel):
    name: str
    description: str


class Dataset(BaseModel):
    name: str
    bucket: str
    namespace: str
    table_name: str
    file_name: str
    description: str | None = None
    file_type: Literal["parquet"] = "parquet"
    num_partitions: int | None = None
    num_rows: int | None = None
    serialized_size: int | None = None

    @property
    def identifier(self: Self) -> str:
        return f"{self.namespace}.{self.table_name}"

    @property
    def location(self: Self) -> str:
        return f"{self.bucket}/{self.file_name}"

    model_config = ConfigDict(from_attributes=True)
