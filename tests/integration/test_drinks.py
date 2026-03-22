from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from modules.drinks.models import Drink
from modules.users.models import User
from services.image import UploadResultDto, get_image_manager
from tests.factories import DrinkFactory, UserFactory


@pytest.fixture
async def drink(db_session: AsyncSession, test_user: User) -> Drink:
    d = DrinkFactory.build(creator_id=test_user.id)
    db_session.add(d)
    await db_session.flush()
    return d


@pytest.fixture
async def global_drink(db_session: AsyncSession) -> Drink:
    d = DrinkFactory.build(creator_id=None)
    db_session.add(d)
    await db_session.flush()
    return d


@pytest.fixture
async def curated_drink(db_session: AsyncSession) -> Drink:
    other = UserFactory.build()
    db_session.add(other)
    await db_session.flush()
    d = DrinkFactory.build(creator_id=other.id, curated=True)
    db_session.add(d)
    await db_session.flush()
    return d


class TestListDrinks:
    async def test_returns_own_drink(self, client: AsyncClient, drink: Drink):
        resp = await client.get("/api/v1/drinks")
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["items"]]
        assert drink.id in ids

    async def test_returns_global_drink(self, client: AsyncClient, global_drink: Drink):
        resp = await client.get("/api/v1/drinks")
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["items"]]
        assert global_drink.id in ids

    async def test_returns_curated_drink(self, client: AsyncClient, curated_drink: Drink):
        resp = await client.get("/api/v1/drinks")
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["items"]]
        assert curated_drink.id in ids

    async def test_mine_filter(self, client: AsyncClient, drink: Drink, global_drink: Drink):
        resp = await client.get("/api/v1/drinks", params={"mine": True})
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["items"]]
        assert drink.id in ids
        assert global_drink.id not in ids

    async def test_pagination(self, client: AsyncClient, db_session: AsyncSession, test_user: User):
        for _ in range(5):
            d = DrinkFactory.build(creator_id=test_user.id)
            db_session.add(d)
        await db_session.flush()

        resp = await client.get("/api/v1/drinks", params={"limit": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] >= 5
        assert data["nextCursor"] is not None

        resp2 = await client.get("/api/v1/drinks", params={"limit": 2, "cursor": data["nextCursor"]})
        assert resp2.status_code == 200
        first_ids = {item["id"] for item in data["items"]}
        second_ids = {item["id"] for item in resp2.json()["items"]}
        assert first_ids.isdisjoint(second_ids)


class TestGetDrink:
    async def test_get_own(self, client: AsyncClient, drink: Drink):
        resp = await client.get(f"/api/v1/drinks/{drink.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == drink.id

    async def test_not_found(self, client: AsyncClient):
        resp = await client.get("/api/v1/drinks/00000000000000000000000000")
        assert resp.status_code == 404


class TestCreateDrink:
    async def test_create(self, client: AsyncClient, test_user: User):
        body = {
            "name": "Green Tea",
            "ph": 7.0,
            "isCarbonated": False,
            "vitamins": {"C": 0.3},
        }
        resp = await client.post("/api/v1/drinks", json=body)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Green Tea"
        assert data["creatorId"] == test_user.id
        assert data["vitamins"] == {"C": 0.3}

    async def test_jsonb_persistence(self, client: AsyncClient):
        body = {
            "name": "Orange Juice",
            "ph": 3.5,
            "vitamins": {"C": 50.0, "A": 10.0},
            "minerals": {"potassium": 200.0},
        }
        resp = await client.post("/api/v1/drinks", json=body)
        assert resp.status_code == 201
        drink_id = resp.json()["id"]

        get_resp = await client.get(f"/api/v1/drinks/{drink_id}")
        data = get_resp.json()
        assert data["vitamins"] == {"C": 50.0, "A": 10.0}
        assert data["minerals"] == {"potassium": 200.0}


class TestUpdateDrink:
    async def test_update_own(self, client: AsyncClient, drink: Drink):
        resp = await client.patch(f"/api/v1/drinks/{drink.id}", json={"name": "Updated"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"

    async def test_cannot_update_global(self, client: AsyncClient, global_drink: Drink):
        resp = await client.patch(f"/api/v1/drinks/{global_drink.id}", json={"name": "Hacked"})
        assert resp.status_code == 403

    async def test_cannot_update_curated(self, client: AsyncClient, curated_drink: Drink):
        resp = await client.patch(f"/api/v1/drinks/{curated_drink.id}", json={"name": "Hacked"})
        assert resp.status_code == 403


class TestDeleteDrink:
    async def test_delete_own(self, client: AsyncClient, drink: Drink):
        resp = await client.delete(f"/api/v1/drinks/{drink.id}")
        assert resp.status_code == 204

        get_resp = await client.get(f"/api/v1/drinks/{drink.id}")
        assert get_resp.status_code == 404

    async def test_cannot_delete_global(self, client: AsyncClient, global_drink: Drink):
        resp = await client.delete(f"/api/v1/drinks/{global_drink.id}")
        assert resp.status_code == 403


class TestUploadDrinkImage:
    @pytest.fixture
    def mock_image_manager(self):
        manager = MagicMock()
        manager.generate_upload_url.return_value = UploadResultDto(
            upload_url="https://s3.example.com/presigned",
            raw_key="raw/drinks/test/abc.jpg",
        )
        return manager

    async def test_upload_returns_presigned_url(self, client: AsyncClient, drink: Drink, app, mock_image_manager):
        app.dependency_overrides[get_image_manager] = lambda: mock_image_manager

        with patch("modules.drinks.handlers.process_drink_image"):
            resp = await client.post(f"/api/v1/drinks/{drink.id}/image?content_type=image/jpeg")

        assert resp.status_code == 200
        data = resp.json()
        assert data["uploadUrl"] == "https://s3.example.com/presigned"
        assert "imageKey" not in data

    async def test_upload_sets_image_key_on_drink(
        self, client: AsyncClient, drink: Drink, db_session: AsyncSession, app, mock_image_manager
    ):
        app.dependency_overrides[get_image_manager] = lambda: mock_image_manager

        with patch("modules.drinks.handlers.process_drink_image"):
            resp = await client.post(f"/api/v1/drinks/{drink.id}/image?content_type=image/png")

        assert resp.status_code == 200
        await db_session.refresh(drink)
        assert drink.image_key == "raw/drinks/test/abc.jpg"

    async def test_upload_dispatches_task_with_countdown(
        self, client: AsyncClient, drink: Drink, app, mock_image_manager
    ):
        app.dependency_overrides[get_image_manager] = lambda: mock_image_manager

        with patch("modules.drinks.handlers.process_drink_image") as mock_task:
            resp = await client.post(f"/api/v1/drinks/{drink.id}/image?content_type=image/jpeg")

        assert resp.status_code == 200
        mock_task.apply_async.assert_called_once_with(
            args=(str(drink.id), "raw/drinks/test/abc.jpg"),
            countdown=settings.s3.image_upload_countdown,
        )

    async def test_cannot_upload_for_global_drink(self, client: AsyncClient, global_drink: Drink):
        resp = await client.post(f"/api/v1/drinks/{global_drink.id}/image?content_type=image/jpeg")
        assert resp.status_code == 403

    async def test_response_includes_image_url(self, client: AsyncClient, drink: Drink):
        resp = await client.get(f"/api/v1/drinks/{drink.id}")
        assert resp.status_code == 200
        assert "imageUrl" in resp.json()
