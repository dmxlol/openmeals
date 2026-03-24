from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status
from ulid import ULID

from core.config import settings
from libs.datetime import utcnow
from libs.locale import Locale
from modules.drinks.dependencies import get_drink_dependency, get_writable_drink_dependency
from modules.drinks.models import Drink, DrinkTranslation
from services.image import UploadResultDto, get_image_manager


def _make_drink(**overrides) -> Drink:
    defaults = {
        "id": str(ULID()),
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


def _make_translation(drink: Drink, name: str = "Test Drink") -> DrinkTranslation:
    return DrinkTranslation(drink_id=drink.id, locale=Locale.EN_US, name=name)


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
    tr = _make_translation(drink)
    count_result = MagicMock()
    count_result.scalar_one.return_value = 1
    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = [drink]
    en_us_result = MagicMock()
    en_us_result.scalars.return_value = [tr]
    mock_db.execute.side_effect = [count_result, items_result, en_us_result]

    response = await client.get("/api/v1/drinks")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Test Drink"
    assert data["items"][0]["ph"] == 7.0


async def test_get_drink(client: AsyncClient, app: FastAPI, mock_db: AsyncMock) -> None:
    drink = _make_drink()
    app.dependency_overrides[get_drink_dependency] = lambda: drink
    tr_result = MagicMock()
    tr_result.scalar_one_or_none.return_value = _make_translation(drink)
    mock_db.execute.return_value = tr_result

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
    assert mock_db.add.call_count == 2  # drink + EN_US translation
    mock_db.commit.assert_awaited_once()


async def test_update_drink(client: AsyncClient, app: FastAPI, mock_db: AsyncMock) -> None:
    drink = _make_drink()
    app.dependency_overrides[get_writable_drink_dependency] = lambda: drink

    with patch("modules.drinks.handlers.generate_drink_embedding"):
        response = await client.patch(f"/api/v1/drinks/{drink.id}", json={"name": "Updated"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Updated"
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


async def test_upload_drink_image(client: AsyncClient, app: FastAPI, mock_db: AsyncMock) -> None:
    drink = _make_drink()
    app.dependency_overrides[get_writable_drink_dependency] = lambda: drink

    mock_manager = MagicMock()
    mock_manager.generate_upload_url.return_value = UploadResultDto(
        upload_url="https://s3.example.com/presigned",
        upload_fields={"key": "raw/drinks/abc/def.jpg", "Content-Type": "image/jpeg"},
        raw_key="raw/drinks/abc/def.jpg",
    )
    app.dependency_overrides[get_image_manager] = lambda: mock_manager

    with patch("modules.drinks.handlers.process_drink_image") as mock_task:
        response = await client.post(f"/api/v1/drinks/{drink.id}/image?content_type=image/jpeg")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["uploadUrl"] == "https://s3.example.com/presigned"
    assert "imageKey" not in data

    mock_manager.generate_upload_url.assert_called_once_with(
        entity_type="drinks",
        entity_id=str(drink.id),
        content_type="image/jpeg",
    )
    assert drink.image_key == "raw/drinks/abc/def.jpg"
    mock_db.commit.assert_awaited_once()
    mock_task.apply_async.assert_called_once_with(
        args=(str(drink.id), "raw/drinks/abc/def.jpg"),
        countdown=settings.s3.image_upload_countdown,
    )


async def test_upload_drink_image_requires_auth(anon_client: AsyncClient) -> None:
    response = await anon_client.post("/api/v1/drinks/00000000000000000000000001/image?content_type=image/jpeg")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_drink_response_includes_image_url(client: AsyncClient, app: FastAPI, mock_db: AsyncMock) -> None:
    drink = _make_drink(image_key="drinks/abc/hash.webp")
    app.dependency_overrides[get_drink_dependency] = lambda: drink
    tr_result = MagicMock()
    tr_result.scalar_one_or_none.return_value = _make_translation(drink)
    mock_db.execute.return_value = tr_result

    response = await client.get(f"/api/v1/drinks/{drink.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "imageUrl" in data
    assert data["imageUrl"].endswith("drinks/abc/hash.webp")
