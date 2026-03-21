import typing as t

from fastapi import Depends
from sqlalchemy import select

from libs.db import check_ingestible_writable, fetch_one_or_raise, ingestible_visible_filter
from libs.types import DBSessionDependency
from modules.foods.models import Food
from modules.users.dependencies import CurrentUserDependency, OptionalUserDependency


async def get_food_dependency(
    food_id: str,
    db: DBSessionDependency,
    user: OptionalUserDependency,
) -> Food:
    return await fetch_one_or_raise(db, select(Food).where(Food.id == food_id, ingestible_visible_filter(Food, user)))


async def get_writable_food_dependency(
    food_id: str,
    db: DBSessionDependency,
    user: CurrentUserDependency,
) -> Food:
    food = await fetch_one_or_raise(db, select(Food).where(Food.id == food_id))
    check_ingestible_writable(food, user)
    return food


FoodDependency = t.Annotated[Food, Depends(get_food_dependency)]
WritableFoodDependency = t.Annotated[Food, Depends(get_writable_food_dependency)]
