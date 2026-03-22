from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from modules.foods.models import Food
from modules.users.models import User
from services.image import UploadResultDto, get_image_manager
from tests.factories import FoodFactory, UserFactory


@pytest.fixture
async def food(db_session: AsyncSession, test_user: User) -> Food:
    f = FoodFactory.build(creator_id=test_user.id)
    db_session.add(f)
    await db_session.flush()
    return f


@pytest.fixture
async def global_food(db_session: AsyncSession) -> Food:
    f = FoodFactory.build(creator_id=None)
    db_session.add(f)
    await db_session.flush()
    return f


@pytest.fixture
async def curated_food(db_session: AsyncSession) -> Food:
    other = UserFactory.build()
    db_session.add(other)
    await db_session.flush()
    f = FoodFactory.build(creator_id=other.id, curated=True)
    db_session.add(f)
    await db_session.flush()
    return f


class TestListFoods:
    async def test_returns_own_food(self, client: AsyncClient, food: Food):
        resp = await client.get("/api/v1/foods")
        assert resp.status_code == 200
        data = resp.json()
        ids = [item["id"] for item in data["items"]]
        assert food.id in ids

    async def test_returns_global_food(self, client: AsyncClient, global_food: Food):
        resp = await client.get("/api/v1/foods")
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["items"]]
        assert global_food.id in ids

    async def test_returns_curated_food(self, client: AsyncClient, curated_food: Food):
        resp = await client.get("/api/v1/foods")
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["items"]]
        assert curated_food.id in ids

    async def test_mine_filter(self, client: AsyncClient, food: Food, global_food: Food):
        resp = await client.get("/api/v1/foods", params={"mine": True})
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["items"]]
        assert food.id in ids
        assert global_food.id not in ids

    async def test_pagination(self, client: AsyncClient, db_session: AsyncSession, test_user: User):
        foods = [FoodFactory.build(creator_id=test_user.id) for _ in range(5)]
        for f in foods:
            db_session.add(f)
        await db_session.flush()

        resp = await client.get("/api/v1/foods", params={"limit": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] >= 5
        assert data["nextCursor"] is not None

        resp2 = await client.get("/api/v1/foods", params={"limit": 2, "cursor": data["nextCursor"]})
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert len(data2["items"]) == 2
        first_page_ids = {item["id"] for item in data["items"]}
        second_page_ids = {item["id"] for item in data2["items"]}
        assert first_page_ids.isdisjoint(second_page_ids)


class TestGetFood:
    async def test_get_own_food(self, client: AsyncClient, food: Food):
        resp = await client.get(f"/api/v1/foods/{food.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == food.id

    async def test_get_global_food(self, client: AsyncClient, global_food: Food):
        resp = await client.get(f"/api/v1/foods/{global_food.id}")
        assert resp.status_code == 200

    async def test_not_found(self, client: AsyncClient):
        resp = await client.get("/api/v1/foods/00000000000000000000000000")
        assert resp.status_code == 404


class TestCreateFood:
    async def test_create(self, client: AsyncClient, test_user: User):
        body = {
            "name": "Banana",
            "proteins": 1.1,
            "carbs": 22.8,
            "fats": 0.3,
            "fibers": 2.6,
            "sugars": 12.2,
            "energy": 89.0,
            "glycemicIndex": 51.0,
            "vitamins": {"B6": 0.4},
            "minerals": {"potassium": 358.0},
        }
        resp = await client.post("/api/v1/foods", json=body)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Banana"
        assert data["creatorId"] == test_user.id
        assert data["vitamins"] == {"B6": 0.4}
        assert data["minerals"] == {"potassium": 358.0}

    async def test_jsonb_persistence(self, client: AsyncClient):
        body = {
            "name": "Apple",
            "proteins": 0.3,
            "carbs": 13.8,
            "fats": 0.2,
            "fibers": 2.4,
            "sugars": 10.4,
            "energy": 52.0,
            "glycemicIndex": 36.0,
            "vitamins": {"C": 4.6, "K": 2.2},
            "minerals": {"calcium": 6.0, "iron": 0.12},
            "nutrients": {"quercetin": 4.0},
        }
        resp = await client.post("/api/v1/foods", json=body)
        assert resp.status_code == 201
        food_id = resp.json()["id"]

        get_resp = await client.get(f"/api/v1/foods/{food_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["vitamins"] == {"C": 4.6, "K": 2.2}
        assert data["minerals"] == {"calcium": 6.0, "iron": 0.12}
        assert data["nutrients"] == {"quercetin": 4.0}


class TestUpdateFood:
    async def test_update_own(self, client: AsyncClient, food: Food):
        resp = await client.patch(f"/api/v1/foods/{food.id}", json={"name": "Updated"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"

    async def test_cannot_update_global(self, client: AsyncClient, global_food: Food):
        resp = await client.patch(f"/api/v1/foods/{global_food.id}", json={"name": "Hacked"})
        assert resp.status_code == 403

    async def test_cannot_update_curated(self, client: AsyncClient, curated_food: Food):
        resp = await client.patch(f"/api/v1/foods/{curated_food.id}", json={"name": "Hacked"})
        assert resp.status_code == 403


class TestDeleteFood:
    async def test_delete_own(self, client: AsyncClient, food: Food):
        resp = await client.delete(f"/api/v1/foods/{food.id}")
        assert resp.status_code == 204

        get_resp = await client.get(f"/api/v1/foods/{food.id}")
        assert get_resp.status_code == 404

    async def test_cannot_delete_global(self, client: AsyncClient, global_food: Food):
        resp = await client.delete(f"/api/v1/foods/{global_food.id}")
        assert resp.status_code == 403

    async def test_cannot_delete_curated(self, client: AsyncClient, curated_food: Food):
        resp = await client.delete(f"/api/v1/foods/{curated_food.id}")
        assert resp.status_code == 403


class TestUploadFoodImage:
    @pytest.fixture
    def mock_image_manager(self):
        manager = MagicMock()
        manager.generate_upload_url.return_value = UploadResultDto(
            upload_url="https://s3.example.com/presigned",
            upload_fields={"key": "raw/foods/test/abc.jpg", "Content-Type": "image/jpeg"},
            raw_key="raw/foods/test/abc.jpg",
        )
        return manager

    async def test_upload_returns_presigned_url(self, client: AsyncClient, food: Food, app, mock_image_manager):
        app.dependency_overrides[get_image_manager] = lambda: mock_image_manager

        with patch("modules.foods.handlers.process_food_image"):
            resp = await client.post(f"/api/v1/foods/{food.id}/image?content_type=image/jpeg")

        assert resp.status_code == 200
        data = resp.json()
        assert data["uploadUrl"] == "https://s3.example.com/presigned"
        assert "imageKey" not in data

    async def test_upload_sets_image_key_on_food(
        self, client: AsyncClient, food: Food, db_session: AsyncSession, app, mock_image_manager
    ):
        app.dependency_overrides[get_image_manager] = lambda: mock_image_manager

        with patch("modules.foods.handlers.process_food_image"):
            resp = await client.post(f"/api/v1/foods/{food.id}/image?content_type=image/png")

        assert resp.status_code == 200
        await db_session.refresh(food)
        assert food.image_key == "raw/foods/test/abc.jpg"

    async def test_upload_dispatches_task_with_countdown(
        self, client: AsyncClient, food: Food, app, mock_image_manager
    ):
        app.dependency_overrides[get_image_manager] = lambda: mock_image_manager

        with patch("modules.foods.handlers.process_food_image") as mock_task:
            resp = await client.post(f"/api/v1/foods/{food.id}/image?content_type=image/jpeg")

        assert resp.status_code == 200
        mock_task.apply_async.assert_called_once_with(
            args=(str(food.id), "raw/foods/test/abc.jpg"),
            countdown=settings.s3.image_upload_countdown,
        )

    async def test_cannot_upload_for_global_food(self, client: AsyncClient, global_food: Food):
        resp = await client.post(f"/api/v1/foods/{global_food.id}/image?content_type=image/jpeg")
        assert resp.status_code == 403

    async def test_response_includes_image_url(self, client: AsyncClient, food: Food):
        resp = await client.get(f"/api/v1/foods/{food.id}")
        assert resp.status_code == 200
        assert "imageUrl" in resp.json()
