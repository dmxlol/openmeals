from fastapi import APIRouter
from sqlalchemy import select
from starlette import status

from core.schemes import CursorPage
from libs.pagination import PaginationDependency, paginate
from libs.types import DBSessionDependency
from modules.drinks.models import Drink
from modules.foods.models import Food
from modules.meals.dependencies import MealDependency, MealDrinkDependency, MealFoodDependency
from modules.meals.models import Meal, MealDrink, MealFood
from modules.meals.schemes import (
    MealCreate,
    MealDrinkCreate,
    MealDrinkResponse,
    MealDrinkUpdate,
    MealFoodCreate,
    MealFoodResponse,
    MealFoodUpdate,
    MealResponse,
    MealUpdate,
)
from modules.users.dependencies import CurrentUserDependency

router = APIRouter(prefix="/meals", tags=["meals"])


@router.get("", response_model=CursorPage[MealResponse])
async def list_meals(
    db: DBSessionDependency,
    user: CurrentUserDependency,
    pagination: PaginationDependency,
) -> CursorPage[Meal]:
    stmt = select(Meal).where(Meal.user_id == user.id)
    return await paginate(db, stmt, Meal, pagination)


@router.get("/{meal_id}")
async def get_meal(
    db: DBSessionDependency,
    meal: MealDependency,
) -> MealResponse:
    foods_result = await db.execute(
        select(MealFood, Food.name.label("food_name"))
        .join(Food, MealFood.food_id == Food.id)
        .where(MealFood.meal_id == meal.id, MealFood.user_id == meal.user_id)
    )
    drinks_result = await db.execute(
        select(MealDrink, Drink.name.label("drink_name"))
        .join(Drink, MealDrink.drink_id == Drink.id)
        .where(MealDrink.meal_id == meal.id, MealDrink.user_id == meal.user_id)
    )
    foods = [
        {**{c.key: getattr(row.MealFood, c.key) for c in MealFood.__table__.columns}, "food_name": row.food_name}
        for row in foods_result.all()
    ]
    drinks = [
        {**{c.key: getattr(row.MealDrink, c.key) for c in MealDrink.__table__.columns}, "drink_name": row.drink_name}
        for row in drinks_result.all()
    ]
    return MealResponse.model_validate(
        {
            **{c.key: getattr(meal, c.key) for c in meal.__table__.columns},
            "foods": foods,
            "drinks": drinks,
        },
    )


@router.post("", response_model=MealResponse, status_code=status.HTTP_201_CREATED)
async def create_meal(
    body: MealCreate,
    db: DBSessionDependency,
    user: CurrentUserDependency,
) -> Meal:
    meal = Meal(**body.model_dump(), user_id=user.id)
    db.add(meal)
    await db.commit()
    await db.refresh(meal)
    return meal


@router.patch("/{meal_id}", response_model=MealResponse)
async def update_meal(
    body: MealUpdate,
    db: DBSessionDependency,
    meal: MealDependency,
) -> Meal:
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(meal, key, value)
    await db.commit()
    await db.refresh(meal)
    return meal


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal(
    db: DBSessionDependency,
    meal: MealDependency,
) -> None:
    await db.delete(meal)
    await db.commit()


# --- Meal Foods ---


@router.post("/{meal_id}/foods", response_model=MealFoodResponse, status_code=status.HTTP_201_CREATED)
async def add_meal_food(
    body: MealFoodCreate,
    db: DBSessionDependency,
    meal: MealDependency,
) -> MealFood:
    meal_food = MealFood(user_id=meal.user_id, meal_id=meal.id, **body.model_dump())
    db.add(meal_food)
    await db.commit()
    await db.refresh(meal_food)
    return meal_food


@router.patch("/{meal_id}/foods/{food_id}", response_model=MealFoodResponse)
async def update_meal_food(
    body: MealFoodUpdate,
    db: DBSessionDependency,
    meal_food: MealFoodDependency,
) -> MealFood:
    meal_food.amount = body.amount
    await db.commit()
    await db.refresh(meal_food)
    return meal_food


@router.delete("/{meal_id}/foods/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_food(
    db: DBSessionDependency,
    meal_food: MealFoodDependency,
) -> None:
    await db.delete(meal_food)
    await db.commit()


# --- Meal Drinks ---


@router.post("/{meal_id}/drinks", response_model=MealDrinkResponse, status_code=status.HTTP_201_CREATED)
async def add_meal_drink(
    body: MealDrinkCreate,
    db: DBSessionDependency,
    meal: MealDependency,
) -> MealDrink:
    meal_drink = MealDrink(user_id=meal.user_id, meal_id=meal.id, **body.model_dump())
    db.add(meal_drink)
    await db.commit()
    await db.refresh(meal_drink)
    return meal_drink


@router.patch("/{meal_id}/drinks/{drink_id}", response_model=MealDrinkResponse)
async def update_meal_drink(
    body: MealDrinkUpdate,
    db: DBSessionDependency,
    meal_drink: MealDrinkDependency,
) -> MealDrink:
    meal_drink.amount = body.amount
    await db.commit()
    await db.refresh(meal_drink)
    return meal_drink


@router.delete("/{meal_id}/drinks/{drink_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_drink(
    db: DBSessionDependency,
    meal_drink: MealDrinkDependency,
) -> None:
    await db.delete(meal_drink)
    await db.commit()
