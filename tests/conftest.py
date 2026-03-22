import os
import typing as t
from unittest.mock import AsyncMock, MagicMock

os.environ["ENVIRONMENT"] = "test"

from dotenv import load_dotenv  # noqa: E402

load_dotenv(".env.test", override=True)

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from core.database import get_db_dependency  # noqa: E402
from core.fastapi import create_app  # noqa: E402


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
