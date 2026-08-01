from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from rest.settings import Settings

settings = Settings()

engine = create_async_engine(settings.db_url.unicode_string())


async def get_conn() -> AsyncIterator[AsyncConnection]:
    async with engine.begin() as conn:
        yield conn


DbConn = Annotated[AsyncConnection, Depends(get_conn)]
