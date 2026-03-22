import typing as t
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from core.config import settings
from core.telemetry import instrument_sqlalchemy


@lru_cache(maxsize=1)
def get_async_engine() -> AsyncEngine:
    async_engine = create_async_engine(settings.database_url.get_secret_value(), echo=False)
    instrument_sqlalchemy(async_engine.sync_engine, settings.otel)
    return async_engine


@lru_cache(maxsize=1)
def get_sync_engine() -> Engine:
    sync_engine = create_engine(settings.database_url.get_secret_value().replace("+asyncpg", "+psycopg"))
    instrument_sqlalchemy(sync_engine, settings.otel)
    return sync_engine


@lru_cache(maxsize=1)
def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_async_engine(), expire_on_commit=False)


async def get_db_dependency() -> t.AsyncGenerator[AsyncSession]:
    async with get_async_session_factory()() as session:
        yield session
