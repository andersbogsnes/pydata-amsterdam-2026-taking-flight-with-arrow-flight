import sqlalchemy as sa
from fastapi import FastAPI, HTTPException, status

from taking_flight.rest.db import messages_table
from taking_flight.rest.dependencies import DbConn
from taking_flight.rest.models import Message

app = FastAPI()

TABLES = {"messages": messages_table}


@app.get("/data/{name}")
async def get_data_from_db(
    name: str, conn: DbConn, num_rows: int | None = None
) -> list[Message]:
    if name not in TABLES:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown table: {name}")

    sql = sa.select(messages_table)
    if num_rows:
        sql = sql.limit(num_rows)
    results = await conn.execute(sql)
    return [Message.model_validate(r) for r in results]
