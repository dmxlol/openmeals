import typing as t

from fastapi import Depends
from sqlalchemy import select

from core.config import settings
from libs.db import fetch_one_or_raise
from libs.types import DBSessionDependency, ULIDStr
from modules.drinks.models import DrinkTranslation
from modules.foods.models import FoodTranslation
from modules.meals.models import Meal, MealDrink, MealFood
from modules.users.dependencies import CurrentUserDependency, LocaleDependency


async def get_meal_dependency(
    meal_id: ULIDStr,
    db: DBSessionDependency,
    user: CurrentUserDependency,
) -> Meal:
    return await fetch_one_or_raise(db, select(Meal).where(Meal.id == meal_id, Meal.user_id == user.id))


async def get_meal_food_dependency(
    meal_id: ULIDStr,
    food_id: ULIDStr,
    db: DBSessionDependency,
    user: CurrentUserDependency,
) -> MealFood:
    return await fetch_one_or_raise(
        db,
        select(MealFood).where(MealFood.meal_id == meal_id, MealFood.food_id == food_id, MealFood.user_id == user.id),
    )


async def get_meal_drink_dependency(
    meal_id: ULIDStr,
    drink_id: ULIDStr,
    db: DBSessionDependency,
    user: CurrentUserDependency,
) -> MealDrink:
    return await fetch_one_or_raise(
        db,
        select(MealDrink).where(
            MealDrink.meal_id == meal_id, MealDrink.drink_id == drink_id, MealDrink.user_id == user.id
        ),
    )


MealDependency = t.Annotated[Meal, Depends(get_meal_dependency)]
MealFoodDependency = t.Annotated[MealFood, Depends(get_meal_food_dependency)]
MealDrinkDependency = t.Annotated[MealDrink, Depends(get_meal_drink_dependency)]


async def get_meal_food_translation_dependency(
    meal_food: MealFoodDependency,
    locale: LocaleDependency,
    db: DBSessionDependency,
) -> FoodTranslation | None:
    result = await db.execute(
        select(FoodTranslation)
        .where(FoodTranslation.food_id == meal_food.food_id)
        .where(FoodTranslation.locale.in_([locale, settings.default_locale]))
        .order_by(FoodTranslation.locale != locale)
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_meal_drink_translation_dependency(
    meal_drink: MealDrinkDependency,
    locale: LocaleDependency,
    db: DBSessionDependency,
) -> DrinkTranslation | None:
    result = await db.execute(
        select(DrinkTranslation)
        .where(DrinkTranslation.drink_id == meal_drink.drink_id)
        .where(DrinkTranslation.locale.in_([locale, settings.default_locale]))
        .order_by(DrinkTranslation.locale != locale)
        .limit(1)
    )
    return result.scalar_one_or_none()


MealFoodTranslationDependency = t.Annotated[FoodTranslation | None, Depends(get_meal_food_translation_dependency)]
MealDrinkTranslationDependency = t.Annotated[DrinkTranslation | None, Depends(get_meal_drink_translation_dependency)]
