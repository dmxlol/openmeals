import logging
import typing as t
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from core.database import AsyncSessionLocal, engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> t.AsyncIterator[None]:
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))
    logger.info("Database connection verified")
    yield
    await engine.dispose()
    logger.info("Database engine disposed")
