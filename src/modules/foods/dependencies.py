import typing as t

from fastapi import Depends
from sqlalchemy import select

from libs.db import fetch_one_or_raise
from libs.types import DBSessionDependency
from modules.foods.models import Food


async def get_food_dependency(
    food_id: str,
    db: DBSessionDependency,
) -> Food:
    return await fetch_one_or_raise(db, select(Food).where(Food.id == food_id))


FoodDependency = t.Annotated[Food, Depends(get_food_dependency)]
