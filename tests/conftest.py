import os
import typing as t
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("CELERY_BROKER_URL", "sqs://localhost")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-api-key")

from core.app import create_app  # noqa: E402
from core.database import get_db_dependency  # noqa: E402


@pytest.fixture
def mock_db() -> AsyncMock:
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
async def client(mock_db: AsyncMock) -> t.AsyncGenerator[AsyncClient]:
    app = create_app()
    app.dependency_overrides[get_db_dependency] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
