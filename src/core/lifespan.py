import logging
import typing as t
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from core.database import get_async_engine, get_async_session_factory

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> t.AsyncIterator[None]:
    async with get_async_session_factory()() as session:
        await session.execute(text("SELECT 1"))
    logger.info("Database connection verified")
    yield
    await get_async_engine().dispose()
    logger.info("Database engine disposed")
