from typing import Annotated, AsyncIterator

from fastapi import Depends
from pyarrow import fs
from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection

from taking_flight.rest.settings import Settings

settings = Settings()

engine = create_async_engine(settings.db_url.unicode_string())


def get_object_store() -> fs.FileSystem:
    return fs.S3FileSystem(
        access_key=settings.access_key.get_secret_value(),
        secret_key=settings.secret_key.get_secret_value(),
        endpoint_override=settings.s3_endpoint.encoded_string(),
        allow_bucket_creation=True,
        region=settings.region,
    )


async def get_conn() -> AsyncIterator[AsyncConnection]:
    async with engine.begin() as conn:
        yield conn


DbConn = Annotated[AsyncConnection, Depends(get_conn)]
FileSystem = Annotated[fs.FileSystem, Depends(get_object_store)]
