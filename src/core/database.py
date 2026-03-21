import typing as t
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import settings

engine = create_async_engine(settings.database_url.get_secret_value(), echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_dependency() -> t.AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


@lru_cache(maxsize=1)
def get_sync_engine() -> Engine:
    return create_engine(settings.database_url.get_secret_value().replace("+asyncpg", "+psycopg"))
