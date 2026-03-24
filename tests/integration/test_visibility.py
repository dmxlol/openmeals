"""Tests for ingestible visibility rules with real DB queries.

Visibility rules:
  - creator_id is None → global, visible to all (including anonymous)
  - curated is True → visible to all (including anonymous)
  - creator_id == user.id → visible only to creator
  - creator_id == other_user.id and not curated → invisible to user
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from libs.locale import Locale
from modules.foods.models import Food, FoodTranslation
from modules.users.models import User
from tests.factories import FoodFactory, UserFactory


async def _add_food(db: AsyncSession, **kwargs) -> Food:
    f = FoodFactory.build(**kwargs)
    db.add(f)
    await db.flush()
    db.add(FoodTranslation(food_id=f.id, locale=Locale.EN_US, name="Test Food"))
    await db.flush()
    return f


@pytest.fixture
async def other_user(db_session: AsyncSession) -> User:
    user = UserFactory.build()
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def global_food(db_session: AsyncSession) -> Food:
    return await _add_food(db_session, creator_id=None, curated=None)


@pytest.fixture
async def curated_food(db_session: AsyncSession, other_user: User) -> Food:
    return await _add_food(db_session, creator_id=other_user.id, curated=True)


@pytest.fixture
async def own_food(db_session: AsyncSession, test_user: User) -> Food:
    return await _add_food(db_session, creator_id=test_user.id)


@pytest.fixture
async def private_food(db_session: AsyncSession, other_user: User) -> Food:
    return await _add_food(db_session, creator_id=other_user.id, curated=None)


class TestAuthenticatedVisibility:
    async def test_sees_global(self, client: AsyncClient, global_food: Food):
        resp = await client.get("/api/v1/foods")
        ids = [item["id"] for item in resp.json()["items"]]
        assert global_food.id in ids

    async def test_sees_curated(self, client: AsyncClient, curated_food: Food):
        resp = await client.get("/api/v1/foods")
        ids = [item["id"] for item in resp.json()["items"]]
        assert curated_food.id in ids

    async def test_sees_own(self, client: AsyncClient, own_food: Food):
        resp = await client.get("/api/v1/foods")
        ids = [item["id"] for item in resp.json()["items"]]
        assert own_food.id in ids

    async def test_cannot_see_others_private(self, client: AsyncClient, private_food: Food):
        resp = await client.get("/api/v1/foods")
        ids = [item["id"] for item in resp.json()["items"]]
        assert private_food.id not in ids

    async def test_cannot_get_others_private_by_id(self, client: AsyncClient, private_food: Food):
        resp = await client.get(f"/api/v1/foods/{private_food.id}")
        assert resp.status_code == 404


class TestAnonymousVisibility:
    async def test_sees_global(self, anon_client: AsyncClient, global_food: Food):
        resp = await anon_client.get("/api/v1/foods")
        ids = [item["id"] for item in resp.json()["items"]]
        assert global_food.id in ids

    async def test_sees_curated(self, anon_client: AsyncClient, curated_food: Food):
        resp = await anon_client.get("/api/v1/foods")
        ids = [item["id"] for item in resp.json()["items"]]
        assert curated_food.id in ids

    async def test_cannot_see_private(self, anon_client: AsyncClient, own_food: Food):
        resp = await anon_client.get("/api/v1/foods")
        ids = [item["id"] for item in resp.json()["items"]]
        assert own_food.id not in ids

    async def test_cannot_get_private_by_id(self, anon_client: AsyncClient, own_food: Food):
        resp = await anon_client.get(f"/api/v1/foods/{own_food.id}")
        assert resp.status_code == 404


class TestWritePermissions:
    async def test_can_update_own(self, client: AsyncClient, own_food: Food):
        resp = await client.patch(f"/api/v1/foods/{own_food.id}", json={"name": "Renamed"})
        assert resp.status_code == 200

    async def test_cannot_update_global(self, client: AsyncClient, global_food: Food):
        resp = await client.patch(f"/api/v1/foods/{global_food.id}", json={"name": "Hacked"})
        assert resp.status_code == 403

    async def test_cannot_update_curated(self, client: AsyncClient, curated_food: Food):
        resp = await client.patch(f"/api/v1/foods/{curated_food.id}", json={"name": "Hacked"})
        assert resp.status_code == 403

    async def test_cannot_update_others_private(self, client: AsyncClient, private_food: Food):
        resp = await client.patch(f"/api/v1/foods/{private_food.id}", json={"name": "Hacked"})
        assert resp.status_code == 403

    async def test_can_delete_own(self, client: AsyncClient, own_food: Food):
        resp = await client.delete(f"/api/v1/foods/{own_food.id}")
        assert resp.status_code == 204

    async def test_cannot_delete_global(self, client: AsyncClient, global_food: Food):
        resp = await client.delete(f"/api/v1/foods/{global_food.id}")
        assert resp.status_code == 403

    async def test_cannot_delete_curated(self, client: AsyncClient, curated_food: Food):
        resp = await client.delete(f"/api/v1/foods/{curated_food.id}")
        assert resp.status_code == 403
