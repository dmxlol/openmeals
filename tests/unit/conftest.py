import typing as t
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID

from core.database import get_db_dependency
from core.fastapi import create_app
from libs.datetime import utcnow
from modules.users.dependencies import get_current_user_dependency, get_optional_user_dependency
from modules.users.models import User


@pytest.fixture
def mock_user() -> User:
    return User(id=str(ULID()), name="Test User", created=utcnow())


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
def app(mock_db: AsyncMock, mock_user: User) -> FastAPI:
    application = create_app()
    application.dependency_overrides[get_db_dependency] = lambda: mock_db
    application.dependency_overrides[get_current_user_dependency] = lambda: mock_user
    application.dependency_overrides[get_optional_user_dependency] = lambda: mock_user
    return application


@pytest.fixture
async def client(app: FastAPI) -> t.AsyncGenerator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
async def anon_client(mock_db: AsyncMock) -> t.AsyncGenerator[AsyncClient]:
    application = create_app()
    application.dependency_overrides[get_db_dependency] = lambda: mock_db
    application.dependency_overrides[get_optional_user_dependency] = lambda: None

    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://test",
    ) as ac:
        yield ac
