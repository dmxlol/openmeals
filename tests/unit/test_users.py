from datetime import date
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status

from libs.datetime import utcnow
from modules.users.dependencies import get_current_user_profile_dependency
from modules.users.models import User, UserProfile

PROFILE_BODY = {"birthday": "2000-01-15", "weight": 75.0, "height": 180.0}


async def test_get_me(client: AsyncClient, mock_user: User) -> None:
    response = await client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(mock_user.id)
    assert data["name"] == "Test User"


async def test_delete_me(client: AsyncClient, mock_db: AsyncMock, mock_user: User) -> None:
    response = await client.delete("/api/v1/users/me")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_db.delete.assert_awaited_once_with(mock_user)
    mock_db.commit.assert_awaited_once()


async def test_get_profile(client: AsyncClient, app: FastAPI, mock_user: User) -> None:
    profile = UserProfile(
        user_id=mock_user.id,
        birthday=date(2000, 1, 15),
        weight=75.0,
        height=180.0,
        created=utcnow(),
        updated=utcnow(),
    )
    app.dependency_overrides[get_current_user_profile_dependency] = lambda: profile

    response = await client.get("/api/v1/users/me/profile")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["weight"] == 75.0
    assert data["height"] == 180.0


async def test_upsert_profile_creates(client: AsyncClient, mock_db: AsyncMock) -> None:
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = result

    response = await client.put("/api/v1/users/me/profile", json=PROFILE_BODY)
    assert response.status_code == status.HTTP_200_OK
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()


async def test_upsert_profile_updates(client: AsyncClient, mock_db: AsyncMock, mock_user: User) -> None:
    profile = UserProfile(
        user_id=mock_user.id,
        birthday=date(2000, 1, 15),
        weight=70.0,
        height=175.0,
        created=utcnow(),
        updated=utcnow(),
    )
    result = MagicMock()
    result.scalar_one_or_none.return_value = profile
    mock_db.execute.return_value = result

    response = await client.put("/api/v1/users/me/profile", json=PROFILE_BODY)
    assert response.status_code == status.HTTP_200_OK
    assert profile.weight == 75.0
    assert profile.height == 180.0
    mock_db.add.assert_not_called()
    mock_db.commit.assert_awaited_once()


async def test_get_me_requires_auth(anon_client: AsyncClient) -> None:
    response = await anon_client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_delete_me_requires_auth(anon_client: AsyncClient) -> None:
    response = await anon_client.delete("/api/v1/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
