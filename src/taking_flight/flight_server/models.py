from pydantic import BaseModel
from pyiceberg.expressions import BooleanExpression
from pyiceberg.table import ALWAYS_TRUE


class DeleteDatasetRequest(BaseModel):
    name: str


class UpdateDatasetRequest(BaseModel):
    name: str
    description: str

class GetDatasetRequest(BaseModel):
    identifier: str
    columns: tuple[str] = ("*",)
    filters: str | BooleanExpression = ALWAYS_TRUE
