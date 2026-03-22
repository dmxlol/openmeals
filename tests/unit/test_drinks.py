from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status
from ulid import ULID

from libs.datetime import utcnow
from modules.drinks.dependencies import get_drink_dependency, get_writable_drink_dependency
from modules.drinks.models import Drink


def _make_drink(**overrides) -> Drink:
    defaults = {
        "id": str(ULID()),
        "name": "Test Drink",
        "ph": 7.0,
        "is_carbonated": False,
        "vitamins": {},
        "minerals": {},
        "nutrients": {},
        "creator_id": None,
        "curated": None,
        "embedding": None,
        "created": utcnow(),
        "updated": utcnow(),
    }
    defaults.update(overrides)
    return Drink(**defaults)


async def test_list_drinks_empty(client: AsyncClient, mock_db: AsyncMock) -> None:
    count_result = MagicMock()
    count_result.scalar_one.return_value = 0
    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = []
    mock_db.execute.side_effect = [count_result, items_result]

    response = await client.get("/api/v1/drinks")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["nextCursor"] is None


async def test_list_drinks_with_items(client: AsyncClient, mock_db: AsyncMock) -> None:
    drink = _make_drink()
    count_result = MagicMock()
    count_result.scalar_one.return_value = 1
    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = [drink]
    mock_db.execute.side_effect = [count_result, items_result]

    response = await client.get("/api/v1/drinks")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Test Drink"
    assert data["items"][0]["ph"] == 7.0


async def test_get_drink(client: AsyncClient, app: FastAPI) -> None:
    drink = _make_drink()
    app.dependency_overrides[get_drink_dependency] = lambda: drink

    response = await client.get(f"/api/v1/drinks/{drink.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Test Drink"
    assert data["ph"] == 7.0
    assert data["id"] == str(drink.id)


async def test_create_drink(client: AsyncClient, mock_db: AsyncMock) -> None:
    body = {
        "name": "New Drink",
        "ph": 6.5,
        "isCarbonated": True,
    }
    with patch("modules.drinks.handlers.generate_drink_embedding"):
        response = await client.post("/api/v1/drinks", json=body)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "New Drink"
    assert data["ph"] == 6.5
    assert data["isCarbonated"] is True
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()


async def test_update_drink(client: AsyncClient, app: FastAPI, mock_db: AsyncMock) -> None:
    drink = _make_drink()
    app.dependency_overrides[get_writable_drink_dependency] = lambda: drink

    with patch("modules.drinks.handlers.generate_drink_embedding"):
        response = await client.patch(f"/api/v1/drinks/{drink.id}", json={"name": "Updated"})
    assert response.status_code == status.HTTP_200_OK
    assert drink.name == "Updated"
    mock_db.commit.assert_awaited_once()


async def test_delete_drink(client: AsyncClient, app: FastAPI, mock_db: AsyncMock) -> None:
    drink = _make_drink()
    app.dependency_overrides[get_writable_drink_dependency] = lambda: drink

    response = await client.delete(f"/api/v1/drinks/{drink.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_db.delete.assert_awaited_once_with(drink)
    mock_db.commit.assert_awaited_once()


async def test_create_drink_requires_auth(anon_client: AsyncClient) -> None:
    response = await anon_client.post("/api/v1/drinks", json={"name": "X", "ph": 7.0})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
