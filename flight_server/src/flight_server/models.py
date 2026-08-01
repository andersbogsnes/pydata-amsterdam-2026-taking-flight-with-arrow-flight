from pydantic import BaseModel

class DeleteDatasetRequest(BaseModel):
    name: str


class UpdateDatasetRequest(BaseModel):
    name: str
    description: str


class GetDatasetRequest(BaseModel):
    identifier: str
    columns: tuple[str] = ("*",)
    filters: str | None = None
