from typing import Literal

from pydantic import BaseModel, ConfigDict


class DeleteDatasetRequest(BaseModel):
    name: str


class UpdateDatasetRequest(BaseModel):
    name: str
    description: str


class Dataset(BaseModel):
    name: str
    bucket: str
    file_name: str
    description: str | None = None
    file_type: Literal["parquet"] = "parquet"
    num_partitions: int | None = None
    num_rows: int | None = None
    serialized_size: int | None = None

    @property
    def location(self) -> str:
        return f"{self.bucket}/{self.file_name}"

    model_config = ConfigDict(from_attributes=True)
