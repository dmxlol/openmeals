import typing as t

from fastapi import Depends
from sqlalchemy import select

from libs.db import check_ingestible_writable, fetch_one_or_raise, ingestible_visible_filter
from libs.types import DBSessionDependency
from modules.drinks.models import Drink
from modules.users.dependencies import CurrentUserDependency, OptionalUserDependency


async def get_drink_dependency(
    drink_id: str,
    db: DBSessionDependency,
    user: OptionalUserDependency,
) -> Drink:
    return await fetch_one_or_raise(
        db, select(Drink).where(Drink.id == drink_id, ingestible_visible_filter(Drink, user))
    )


async def get_writable_drink_dependency(
    drink_id: str,
    db: DBSessionDependency,
    user: CurrentUserDependency,
) -> Drink:
    drink = await fetch_one_or_raise(db, select(Drink).where(Drink.id == drink_id))
    check_ingestible_writable(drink, user)
    return drink


DrinkDependency = t.Annotated[Drink, Depends(get_drink_dependency)]
WritableDrinkDependency = t.Annotated[Drink, Depends(get_writable_drink_dependency)]
