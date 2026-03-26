from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError
from starlette import status
from ulid import ULID

from libs.datetime import utcnow
from modules.meals.dependencies import get_meal_dependency
from modules.meals.models import Meal, MealDrink, MealFood
from modules.users.models import User


def _make_meal(user_id: str, **overrides) -> Meal:
    defaults = {
        "id": str(ULID()),
        "name": "Test Meal",
        "user_id": user_id,
        "created": utcnow(),
        "updated": utcnow(),
    }
    defaults.update(overrides)
    return Meal(**defaults)


async def test_list_meals_empty(client: AsyncClient, mock_db: AsyncMock) -> None:
    count_result = MagicMock()
    count_result.scalar_one.return_value = 0
    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = []
    mock_db.execute.side_effect = [count_result, items_result]

    response = await client.get("/api/v1/meals")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


async def test_list_meals_with_items(client: AsyncClient, mock_db: AsyncMock, mock_user: User) -> None:
    meal = _make_meal(mock_user.id)
    count_result = MagicMock()
    count_result.scalar_one.return_value = 1
    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = [meal]
    mock_db.execute.side_effect = [count_result, items_result]

    response = await client.get("/api/v1/meals")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Test Meal"


async def test_get_meal(client: AsyncClient, app: FastAPI, mock_db: AsyncMock, mock_user: User) -> None:
    meal = _make_meal(mock_user.id)
    app.dependency_overrides[get_meal_dependency] = lambda: meal

    foods_result = MagicMock()
    foods_result.all.return_value = []
    drinks_result = MagicMock()
    drinks_result.all.return_value = []
    mock_db.execute.side_effect = [foods_result, drinks_result]

    response = await client.get(f"/api/v1/meals/{meal.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Test Meal"
    assert data["foods"] == []
    assert data["drinks"] == []


async def test_get_meal_with_foods_and_drinks(
    client: AsyncClient,
    app: FastAPI,
    mock_db: AsyncMock,
    mock_user: User,
) -> None:
    meal = _make_meal(mock_user.id)
    food_id = str(ULID())
    drink_id = str(ULID())
    meal_food = MealFood(user_id=mock_user.id, meal_id=meal.id, food_id=food_id, amount=150.0)
    meal_drink = MealDrink(user_id=mock_user.id, meal_id=meal.id, drink_id=drink_id, amount=250.0)
    app.dependency_overrides[get_meal_dependency] = lambda: meal

    food_row = MagicMock()
    food_row.MealFood = meal_food
    food_row.food_image_key = None
    foods_result = MagicMock()
    foods_result.all.return_value = [food_row]

    drink_row = MagicMock()
    drink_row.MealDrink = meal_drink
    drink_row.drink_image_key = None
    drinks_result = MagicMock()
    drinks_result.all.return_value = [drink_row]

    food_names_result = MagicMock()
    food_names_result.all.return_value = [(food_id, "Chicken Breast")]
    drink_names_result = MagicMock()
    drink_names_result.all.return_value = [(drink_id, "Green Tea")]

    mock_db.execute.side_effect = [foods_result, drinks_result, food_names_result, drink_names_result]

    response = await client.get(f"/api/v1/meals/{meal.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["foods"]) == 1
    assert data["foods"][0]["foodId"] == food_id
    assert data["foods"][0]["foodName"] == "Chicken Breast"
    assert data["foods"][0]["amount"] == 150.0
    assert len(data["drinks"]) == 1
    assert data["drinks"][0]["drinkId"] == drink_id
    assert data["drinks"][0]["drinkName"] == "Green Tea"
    assert data["drinks"][0]["amount"] == 250.0


async def test_create_meal(client: AsyncClient, mock_db: AsyncMock) -> None:
    response = await client.post("/api/v1/meals", json={"name": "Lunch"})
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Lunch"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()


async def test_delete_meal(client: AsyncClient, app: FastAPI, mock_db: AsyncMock, mock_user: User) -> None:
    meal = _make_meal(mock_user.id)
    app.dependency_overrides[get_meal_dependency] = lambda: meal

    response = await client.delete(f"/api/v1/meals/{meal.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_db.delete.assert_awaited_once_with(meal)


async def test_list_meals_requires_auth(anon_client: AsyncClient) -> None:
    response = await anon_client.get("/api/v1/meals")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_create_meal_requires_auth(anon_client: AsyncClient) -> None:
    response = await anon_client.post("/api/v1/meals", json={"name": "X"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_add_food_to_meal(client: AsyncClient, app: FastAPI, mock_db: AsyncMock, mock_user: User) -> None:
    meal = _make_meal(mock_user.id)
    app.dependency_overrides[get_meal_dependency] = lambda: meal
    food_id = str(ULID())
    food_mock = MagicMock()
    food_mock.image_key = None
    translation_mock = MagicMock()
    translation_mock.name = "Banana"
    translation_mock.food_id = food_id
    mock_db.get.return_value = food_mock
    tr_result = MagicMock()
    tr_result.scalars.return_value = [translation_mock]
    mock_db.execute.return_value = tr_result

    response = await client.post(f"/api/v1/meals/{meal.id}/foods", json={"foodId": food_id, "amount": 150.0})

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["foodId"] == food_id
    assert data["foodName"] == "Banana"
    assert data["amount"] == 150.0
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()


async def test_add_duplicate_food_returns_conflict(
    client: AsyncClient, app: FastAPI, mock_db: AsyncMock, mock_user: User
) -> None:
    meal = _make_meal(mock_user.id)
    app.dependency_overrides[get_meal_dependency] = lambda: meal
    orig = MagicMock()
    orig.sqlstate = "23505"
    mock_db.commit.side_effect = IntegrityError("stmt", {}, orig)

    response = await client.post(f"/api/v1/meals/{meal.id}/foods", json={"foodId": str(ULID()), "amount": 100.0})

    assert response.status_code == status.HTTP_409_CONFLICT


async def test_add_drink_to_meal(client: AsyncClient, app: FastAPI, mock_db: AsyncMock, mock_user: User) -> None:
    meal = _make_meal(mock_user.id)
    app.dependency_overrides[get_meal_dependency] = lambda: meal
    drink_id = str(ULID())
    drink_mock = MagicMock()
    drink_mock.image_key = None
    translation_mock = MagicMock()
    translation_mock.name = "Green Tea"
    translation_mock.drink_id = drink_id
    mock_db.get.return_value = drink_mock
    tr_result = MagicMock()
    tr_result.scalars.return_value = [translation_mock]
    mock_db.execute.return_value = tr_result

    response = await client.post(f"/api/v1/meals/{meal.id}/drinks", json={"drinkId": drink_id, "amount": 250.0})

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["drinkId"] == drink_id
    assert data["drinkName"] == "Green Tea"
    assert data["amount"] == 250.0
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()


async def test_add_duplicate_drink_returns_conflict(
    client: AsyncClient, app: FastAPI, mock_db: AsyncMock, mock_user: User
) -> None:
    meal = _make_meal(mock_user.id)
    app.dependency_overrides[get_meal_dependency] = lambda: meal
    orig = MagicMock()
    orig.sqlstate = "23505"
    mock_db.commit.side_effect = IntegrityError("stmt", {}, orig)

    response = await client.post(f"/api/v1/meals/{meal.id}/drinks", json={"drinkId": str(ULID()), "amount": 200.0})

    assert response.status_code == status.HTTP_409_CONFLICT
