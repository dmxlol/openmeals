from fastapi import APIRouter
from sqlalchemy import select
from starlette import status

from libs.types import DBSessionDependency
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

router = APIRouter(prefix="/meals", tags=["meals"])


@router.get("", response_model=list[MealResponse])
async def list_meals(
    db: DBSessionDependency,
) -> list[Meal]:
    # TODO: filter by current user
    result = await db.execute(select(Meal))
    return list(result.scalars().all())


@router.get("/{meal_id}", response_model=MealResponse)
async def get_meal(
    meal: MealDependency,
) -> Meal:
    return meal


@router.post("", response_model=MealResponse, status_code=status.HTTP_201_CREATED)
async def create_meal(
    body: MealCreate,
    db: DBSessionDependency,
) -> Meal:
    # TODO: set user_id from current user
    meal = Meal(**body.model_dump(), user_id="stub")
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
    meal_id: str,
    body: MealFoodCreate,
    db: DBSessionDependency,
) -> MealFood:
    # TODO: set user_id from current user
    meal_food = MealFood(user_id="stub", meal_id=meal_id, **body.model_dump())
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
    meal_id: str,
    body: MealDrinkCreate,
    db: DBSessionDependency,
) -> MealDrink:
    # TODO: set user_id from current user
    meal_drink = MealDrink(user_id="stub", meal_id=meal_id, **body.model_dump())
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
