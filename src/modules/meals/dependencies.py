import typing as t

from fastapi import Depends
from sqlalchemy import select

from libs.db import fetch_one_or_raise
from libs.types import DBSessionDependency
from modules.meals.models import Meal, MealDrink, MealFood


async def get_meal_dependency(
    meal_id: str,
    db: DBSessionDependency,
) -> Meal:
    return await fetch_one_or_raise(db, select(Meal).where(Meal.id == meal_id))


async def get_meal_food_dependency(
    meal_id: str,
    food_id: str,
    db: DBSessionDependency,
) -> MealFood:
    return await fetch_one_or_raise(
        db,
        select(MealFood).where(MealFood.meal_id == meal_id, MealFood.food_id == food_id),
    )


async def get_meal_drink_dependency(
    meal_id: str,
    drink_id: str,
    db: DBSessionDependency,
) -> MealDrink:
    return await fetch_one_or_raise(
        db,
        select(MealDrink).where(MealDrink.meal_id == meal_id, MealDrink.drink_id == drink_id),
    )


MealDependency = t.Annotated[Meal, Depends(get_meal_dependency)]
MealFoodDependency = t.Annotated[MealFood, Depends(get_meal_food_dependency)]
MealDrinkDependency = t.Annotated[MealDrink, Depends(get_meal_drink_dependency)]
