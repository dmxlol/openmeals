import typing as t

import psycopg
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

from core.celery import celery_app
from core.config import settings
from core.database import get_db_dependency
from core.fastapi import create_app
from libs.app import AppRegistry
from modules.users.dependencies import get_current_user_dependency, get_optional_user_dependency
from modules.users.models import User
from tests.factories import UserFactory

TEST_DB_URL = settings.database_url.get_secret_value()
SYNC_ADMIN_DSN = "host=localhost port=5432 user=nutrition password=nutrition dbname=nutrition"

_db_created = False


def _ensure_test_database() -> None:
    global _db_created
    if _db_created:
        return
    with psycopg.connect(SYNC_ADMIN_DSN, autocommit=True) as conn:
        row = conn.execute("SELECT 1 FROM pg_database WHERE datname = 'test_openmeals'").fetchone()
        if row is None:
            conn.execute("CREATE DATABASE test_openmeals")
    _db_created = True


_tables_created = False


async def _create_tables(engine) -> None:
    global _tables_created
    if _tables_created:
        return
    registry = AppRegistry()
    registry.get_all_models()
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(SQLModel.metadata.create_all)
    _tables_created = True


# Configure celery eager mode once
celery_app.conf.update(
    task_always_eager=True,
    task_eager_propagates=False,
)


@pytest.fixture
async def db_session() -> t.AsyncGenerator[AsyncSession]:
    """SAVEPOINT-based session isolation.

    Opens a real connection, begins a transaction, then binds the session
    to that connection. Every ``session.commit()`` inside the test only
    releases a SAVEPOINT — the outer transaction is rolled back at the end.
    """
    _ensure_test_database()

    engine = create_async_engine(TEST_DB_URL, echo=False)
    await _create_tables(engine)

    async with engine.connect() as conn:
        trans = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)

        await conn.begin_nested()

        @event.listens_for(session.sync_session, "after_transaction_end")
        def restart_savepoint(session_sync, transaction):
            if transaction.nested and not transaction._parent.nested:
                session_sync.begin_nested()

        yield session

        await session.close()
        await trans.rollback()

    await engine.dispose()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = UserFactory.build()
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def client(db_session: AsyncSession, test_user: User) -> t.AsyncGenerator[AsyncClient]:
    app = create_app()

    app.dependency_overrides[get_db_dependency] = lambda: db_session
    app.dependency_overrides[get_current_user_dependency] = lambda: test_user
    app.dependency_overrides[get_optional_user_dependency] = lambda: test_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
async def anon_client(db_session: AsyncSession) -> t.AsyncGenerator[AsyncClient]:
    app = create_app()

    app.dependency_overrides[get_db_dependency] = lambda: db_session
    app.dependency_overrides[get_optional_user_dependency] = lambda: None

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
