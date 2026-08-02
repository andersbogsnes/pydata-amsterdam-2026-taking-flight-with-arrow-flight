from collections.abc import AsyncIterable

import sqlalchemy as sa
from fastapi import Depends, FastAPI, HTTPException

from rest import auth, db
from rest.dependencies import DbConn
from rest.models import Ride

app = FastAPI(dependencies=[Depends(auth.verify_user)])


@app.get("/health")
async def health_check(conn: DbConn):
    r = await conn.execute(sa.text("SELECT 1"))
    if r.scalar_one():
        return {"status": "ok", "db": "ok"}
    else:
        raise HTTPException(status_code=500, detail="Database Error")


@app.get("/data/rides/streaming")
async def get_streaming_data_from_db(
    conn: DbConn, num_rows: int | None = None
) -> AsyncIterable[Ride]:

    sql = sa.select(db.rides_table)
    if num_rows:
        sql = sql.limit(num_rows)
    async with conn.stream(sql) as stream:
        async for result in stream:
            yield Ride.model_validate(result, from_attributes=True)


@app.get("/data/rides/all")
async def get_all_rides_from_db(
    conn: DbConn, num_rows: int | None = None
) -> list[Ride]:
    sql = sa.select(db.rides_table)
    if num_rows:
        sql = sql.limit(num_rows)
    r = await conn.execute(sql)
    return [Ride.model_validate(r, from_attributes=True) for r in r]
