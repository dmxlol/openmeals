import typing as t

from fastapi import Depends
from sqlalchemy import select

from core.config import settings
from libs.db import check_ingestible_writable, fetch_one_or_raise, ingestible_visible_filter
from libs.types import DBSessionDependency, ULIDStr
from modules.foods.models import Food, FoodTranslation
from modules.users.dependencies import CurrentUserDependency, LocaleDependency, OptionalUserDependency


async def get_food_dependency(
    food_id: ULIDStr,
    db: DBSessionDependency,
    user: OptionalUserDependency,
) -> Food:
    return await fetch_one_or_raise(db, select(Food).where(Food.id == food_id, ingestible_visible_filter(Food, user)))


async def get_writable_food_dependency(
    food_id: ULIDStr,
    db: DBSessionDependency,
    user: CurrentUserDependency,
) -> Food:
    food = await fetch_one_or_raise(db, select(Food).where(Food.id == food_id))
    check_ingestible_writable(food, user)
    return food


FoodDependency = t.Annotated[Food, Depends(get_food_dependency)]
WritableFoodDependency = t.Annotated[Food, Depends(get_writable_food_dependency)]


async def get_food_translation_dependency(
    food: FoodDependency,
    locale: LocaleDependency,
    db: DBSessionDependency,
) -> FoodTranslation | None:
    result = await db.execute(
        select(FoodTranslation)
        .where(FoodTranslation.food_id == food.id, FoodTranslation.locale.in_([locale, settings.default_locale]))
        .order_by(FoodTranslation.locale != locale)
        .limit(1)
    )
    return result.scalar_one_or_none()


FoodTranslationDependency = t.Annotated[FoodTranslation | None, Depends(get_food_translation_dependency)]
