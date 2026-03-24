from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status
from ulid import ULID

from core.config import settings
from libs.datetime import utcnow
from libs.locale import Locale
from modules.foods.dependencies import get_food_dependency, get_writable_food_dependency
from modules.foods.models import Food, FoodTranslation
from services.image import UploadResultDto, get_image_manager


def _make_food(**overrides) -> Food:
    defaults = {
        "id": str(ULID()),
        "proteins": 10.0,
        "carbs": 20.0,
        "fats": 5.0,
        "fibers": 3.0,
        "sugars": 2.0,
        "energy": 150.0,
        "glycemic_index": 50.0,
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
    return Food(**defaults)


def _make_translation(food: Food, name: str = "Test Food") -> FoodTranslation:
    return FoodTranslation(food_id=food.id, locale=Locale.EN_US, name=name)


async def test_list_foods_empty(client: AsyncClient, mock_db: AsyncMock) -> None:
    count_result = MagicMock()
    count_result.scalar_one.return_value = 0
    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = []
    mock_db.execute.side_effect = [count_result, items_result]

    response = await client.get("/api/v1/foods")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["nextCursor"] is None


async def test_list_foods_with_items(client: AsyncClient, mock_db: AsyncMock) -> None:
    food = _make_food()
    tr = _make_translation(food)
    count_result = MagicMock()
    count_result.scalar_one.return_value = 1
    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = [food]
    en_us_result = MagicMock()
    en_us_result.scalars.return_value = [tr]
    mock_db.execute.side_effect = [count_result, items_result, en_us_result]

    response = await client.get("/api/v1/foods")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Test Food"
    assert data["items"][0]["proteins"] == 10.0


async def test_get_food(client: AsyncClient, app: FastAPI, mock_db: AsyncMock) -> None:
    food = _make_food()
    app.dependency_overrides[get_food_dependency] = lambda: food
    tr_result = MagicMock()
    tr_result.scalar_one_or_none.return_value = _make_translation(food)
    mock_db.execute.return_value = tr_result

    response = await client.get(f"/api/v1/foods/{food.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Test Food"
    assert data["proteins"] == 10.0
    assert data["id"] == str(food.id)


async def test_get_food_with_jsonb(client: AsyncClient, app: FastAPI, mock_db: AsyncMock) -> None:
    food = _make_food(vitamins={"A": 100.0, "C": 50.0}, minerals={"iron": 8.0})
    app.dependency_overrides[get_food_dependency] = lambda: food
    tr_result = MagicMock()
    tr_result.scalar_one_or_none.return_value = _make_translation(food)
    mock_db.execute.return_value = tr_result

    response = await client.get(f"/api/v1/foods/{food.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["vitamins"] == {"A": 100.0, "C": 50.0}
    assert data["minerals"] == {"iron": 8.0}


async def test_create_food(client: AsyncClient, mock_db: AsyncMock) -> None:
    body = {
        "name": "New Food",
        "proteins": 5.0,
        "carbs": 10.0,
        "fats": 2.0,
        "fibers": 1.0,
        "sugars": 0.5,
        "energy": 80.0,
        "glycemicIndex": 30.0,
    }
    with patch("modules.foods.handlers.generate_food_embedding"):
        response = await client.post("/api/v1/foods", json=body)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "New Food"
    assert data["proteins"] == 5.0
    assert data["id"] is not None
    assert mock_db.add.call_count == 2  # food + EN_US translation
    mock_db.commit.assert_awaited_once()


async def test_update_food(client: AsyncClient, app: FastAPI, mock_db: AsyncMock) -> None:
    food = _make_food()
    app.dependency_overrides[get_writable_food_dependency] = lambda: food

    with patch("modules.foods.handlers.generate_food_embedding"):
        response = await client.patch(f"/api/v1/foods/{food.id}", json={"name": "Updated"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Updated"
    mock_db.commit.assert_awaited_once()


async def test_delete_food(client: AsyncClient, app: FastAPI, mock_db: AsyncMock) -> None:
    food = _make_food()
    app.dependency_overrides[get_writable_food_dependency] = lambda: food

    response = await client.delete(f"/api/v1/foods/{food.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_db.delete.assert_awaited_once_with(food)
    mock_db.commit.assert_awaited_once()


async def test_list_foods_requires_no_auth(anon_client: AsyncClient, mock_db: AsyncMock) -> None:
    count_result = MagicMock()
    count_result.scalar_one.return_value = 0
    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = []
    mock_db.execute.side_effect = [count_result, items_result]

    response = await anon_client.get("/api/v1/foods")
    assert response.status_code == status.HTTP_200_OK


async def test_create_food_requires_auth(anon_client: AsyncClient) -> None:
    body = {
        "name": "X",
        "proteins": 1,
        "carbs": 1,
        "fats": 1,
        "fibers": 1,
        "sugars": 1,
        "energy": 1,
        "glycemicIndex": 1,
    }
    response = await anon_client.post("/api/v1/foods", json=body)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_upload_food_image(client: AsyncClient, app: FastAPI, mock_db: AsyncMock) -> None:
    food = _make_food()
    app.dependency_overrides[get_writable_food_dependency] = lambda: food

    mock_manager = MagicMock()
    mock_manager.generate_upload_url.return_value = UploadResultDto(
        upload_url="https://s3.example.com/presigned",
        upload_fields={"key": "raw/foods/abc/def.jpg", "Content-Type": "image/jpeg"},
        raw_key="raw/foods/abc/def.jpg",
    )
    app.dependency_overrides[get_image_manager] = lambda: mock_manager

    with patch("modules.foods.handlers.process_food_image") as mock_task:
        response = await client.post(f"/api/v1/foods/{food.id}/image?content_type=image/jpeg")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["uploadUrl"] == "https://s3.example.com/presigned"
    assert "imageKey" not in data

    mock_manager.generate_upload_url.assert_called_once_with(
        entity_type="foods",
        entity_id=str(food.id),
        content_type="image/jpeg",
    )
    assert food.image_key == "raw/foods/abc/def.jpg"
    mock_db.commit.assert_awaited_once()
    mock_task.apply_async.assert_called_once_with(
        args=(str(food.id), "raw/foods/abc/def.jpg"),
        countdown=settings.s3.image_upload_countdown,
    )


async def test_upload_food_image_requires_auth(anon_client: AsyncClient) -> None:
    response = await anon_client.post("/api/v1/foods/00000000000000000000000001/image?content_type=image/jpeg")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_food_response_includes_image_url(client: AsyncClient, app: FastAPI, mock_db: AsyncMock) -> None:
    food = _make_food(image_key="foods/abc/hash.webp")
    app.dependency_overrides[get_food_dependency] = lambda: food
    tr_result = MagicMock()
    tr_result.scalar_one_or_none.return_value = _make_translation(food)
    mock_db.execute.return_value = tr_result

    response = await client.get(f"/api/v1/foods/{food.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "imageUrl" in data
    assert data["imageUrl"].endswith("foods/abc/hash.webp")
