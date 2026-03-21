import typing as t

from fastapi import Depends
from sqlalchemy import select

from libs.db import fetch_one_or_raise
from libs.types import DBSessionDependency
from modules.drinks.models import Drink


async def get_drink_dependency(
    drink_id: str,
    db: DBSessionDependency,
) -> Drink:
    return await fetch_one_or_raise(db, select(Drink).where(Drink.id == drink_id))


DrinkDependency = t.Annotated[Drink, Depends(get_drink_dependency)]
