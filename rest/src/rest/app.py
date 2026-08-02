from collections.abc import AsyncIterable

import sqlalchemy as sa
from fastapi import Depends, FastAPI, HTTPException, status

from rest import auth, db
from rest.dependencies import DbConn
from rest.models import Message

app = FastAPI(dependencies=[Depends(auth.verify_user)])

TABLES = {"messages": db.messages_table}


@app.get("/data/{name}")
async def get_data_from_db(
    name: str, conn: DbConn, num_rows: int | None = None
) -> AsyncIterable[Message]:
    if name not in TABLES:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown table: {name}")

    sql = sa.select(db.messages_table)
    if num_rows:
        sql = sql.limit(num_rows)
    async with conn.stream(sql) as stream:
        async for result in stream:
            yield Message.model_validate(result, from_attributes=True)
