from pydantic import BaseModel


class CreateNamespaceRequest(BaseModel):
    name: str


class DeleteDatasetRequest(BaseModel):
    name: str


class UpdateDatasetRequest(BaseModel):
    name: str
    description: str


class GetDatasetRequest(BaseModel):
    identifier: str
    columns: tuple[str] = ("*",)
    filters: str | None = None


class DoPutResponse(BaseModel):
    rows_inserted: int | None = None
    total_rows: int
