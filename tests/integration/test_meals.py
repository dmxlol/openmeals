import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from modules.drinks.models import Drink
from modules.foods.models import Food
from modules.meals.models import Meal
from modules.users.models import User
from tests.factories import DrinkFactory, FoodFactory, MealFactory, UserFactory


@pytest.fixture
async def meal(db_session: AsyncSession, test_user: User) -> Meal:
    m = MealFactory.build(user_id=test_user.id)
    db_session.add(m)
    await db_session.flush()
    return m


@pytest.fixture
async def food(db_session: AsyncSession, test_user: User) -> Food:
    f = FoodFactory.build(creator_id=test_user.id)
    db_session.add(f)
    await db_session.flush()
    return f


@pytest.fixture
async def drink(db_session: AsyncSession, test_user: User) -> Drink:
    d = DrinkFactory.build(creator_id=test_user.id)
    db_session.add(d)
    await db_session.flush()
    return d


class TestListMeals:
    async def test_list_own_meals(self, client: AsyncClient, meal: Meal):
        resp = await client.get("/api/v1/meals")
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["items"]]
        assert meal.id in ids

    async def test_cannot_see_other_users_meals(self, client: AsyncClient, db_session: AsyncSession):
        other = UserFactory.build()
        db_session.add(other)
        await db_session.flush()
        other_meal = MealFactory.build(user_id=other.id)
        db_session.add(other_meal)
        await db_session.flush()

        resp = await client.get("/api/v1/meals")
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["items"]]
        assert other_meal.id not in ids

    async def test_pagination(self, client: AsyncClient, db_session: AsyncSession, test_user: User):
        for _ in range(5):
            m = MealFactory.build(user_id=test_user.id)
            db_session.add(m)
        await db_session.flush()

        resp = await client.get("/api/v1/meals", params={"limit": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] >= 5
        assert data["nextCursor"] is not None


class TestGetMeal:
    async def test_get_own(self, client: AsyncClient, meal: Meal):
        resp = await client.get(f"/api/v1/meals/{meal.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == meal.id
        assert data["foods"] == []
        assert data["drinks"] == []

    async def test_get_with_foods_and_drinks(
        self, client: AsyncClient, meal: Meal, food: Food, drink: Drink
    ):
        await client.post(f"/api/v1/meals/{meal.id}/foods", json={"foodId": food.id, "amount": 100.0})
        await client.post(f"/api/v1/meals/{meal.id}/drinks", json={"drinkId": drink.id, "amount": 250.0})

        resp = await client.get(f"/api/v1/meals/{meal.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["foods"]) == 1
        assert data["foods"][0]["foodId"] == food.id
        assert data["foods"][0]["amount"] == 100.0
        assert len(data["drinks"]) == 1
        assert data["drinks"][0]["drinkId"] == drink.id
        assert data["drinks"][0]["amount"] == 250.0

    async def test_cannot_get_other_users_meal(self, client: AsyncClient, db_session: AsyncSession):
        other = UserFactory.build()
        db_session.add(other)
        await db_session.flush()
        other_meal = MealFactory.build(user_id=other.id)
        db_session.add(other_meal)
        await db_session.flush()

        resp = await client.get(f"/api/v1/meals/{other_meal.id}")
        assert resp.status_code == 404


class TestCreateMeal:
    async def test_create(self, client: AsyncClient, test_user: User):
        resp = await client.post("/api/v1/meals", json={"name": "Breakfast"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Breakfast"
        assert data["userId"] == test_user.id


class TestUpdateMeal:
    async def test_update(self, client: AsyncClient, meal: Meal):
        resp = await client.patch(f"/api/v1/meals/{meal.id}", json={"name": "Dinner"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Dinner"


class TestDeleteMeal:
    async def test_delete(self, client: AsyncClient, meal: Meal):
        resp = await client.delete(f"/api/v1/meals/{meal.id}")
        assert resp.status_code == 204

        get_resp = await client.get(f"/api/v1/meals/{meal.id}")
        assert get_resp.status_code == 404


class TestMealFoods:
    async def test_add_food_to_meal(self, client: AsyncClient, meal: Meal, food: Food):
        resp = await client.post(
            f"/api/v1/meals/{meal.id}/foods",
            json={"foodId": food.id, "amount": 150.0},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["foodId"] == food.id
        assert data["amount"] == 150.0

    async def test_update_meal_food(self, client: AsyncClient, meal: Meal, food: Food):
        await client.post(
            f"/api/v1/meals/{meal.id}/foods",
            json={"foodId": food.id, "amount": 100.0},
        )
        resp = await client.patch(
            f"/api/v1/meals/{meal.id}/foods/{food.id}",
            json={"amount": 200.0},
        )
        assert resp.status_code == 200
        assert resp.json()["amount"] == 200.0

    async def test_delete_meal_food(self, client: AsyncClient, meal: Meal, food: Food):
        await client.post(
            f"/api/v1/meals/{meal.id}/foods",
            json={"foodId": food.id, "amount": 100.0},
        )
        resp = await client.delete(f"/api/v1/meals/{meal.id}/foods/{food.id}")
        assert resp.status_code == 204


class TestMealDrinks:
    async def test_add_drink_to_meal(self, client: AsyncClient, meal: Meal, drink: Drink):
        resp = await client.post(
            f"/api/v1/meals/{meal.id}/drinks",
            json={"drinkId": drink.id, "amount": 250.0},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["drinkId"] == drink.id
        assert data["amount"] == 250.0

    async def test_update_meal_drink(self, client: AsyncClient, meal: Meal, drink: Drink):
        await client.post(
            f"/api/v1/meals/{meal.id}/drinks",
            json={"drinkId": drink.id, "amount": 250.0},
        )
        resp = await client.patch(
            f"/api/v1/meals/{meal.id}/drinks/{drink.id}",
            json={"amount": 500.0},
        )
        assert resp.status_code == 200
        assert resp.json()["amount"] == 500.0

    async def test_delete_meal_drink(self, client: AsyncClient, meal: Meal, drink: Drink):
        await client.post(
            f"/api/v1/meals/{meal.id}/drinks",
            json={"drinkId": drink.id, "amount": 250.0},
        )
        resp = await client.delete(f"/api/v1/meals/{meal.id}/drinks/{drink.id}")
        assert resp.status_code == 204
