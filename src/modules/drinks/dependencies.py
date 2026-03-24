import typing as t

from fastapi import Depends
from sqlalchemy import select

from core.config import settings
from libs.db import check_ingestible_writable, fetch_one_or_raise, ingestible_visible_filter
from libs.types import DBSessionDependency, ULIDStr
from modules.drinks.models import Drink, DrinkTranslation
from modules.users.dependencies import CurrentUserDependency, LocaleDependency, OptionalUserDependency


async def get_drink_dependency(
    drink_id: ULIDStr,
    db: DBSessionDependency,
    user: OptionalUserDependency,
) -> Drink:
    return await fetch_one_or_raise(
        db, select(Drink).where(Drink.id == drink_id, ingestible_visible_filter(Drink, user))
    )


async def get_writable_drink_dependency(
    drink_id: ULIDStr,
    db: DBSessionDependency,
    user: CurrentUserDependency,
) -> Drink:
    drink = await fetch_one_or_raise(db, select(Drink).where(Drink.id == drink_id))
    check_ingestible_writable(drink, user)
    return drink


DrinkDependency = t.Annotated[Drink, Depends(get_drink_dependency)]
WritableDrinkDependency = t.Annotated[Drink, Depends(get_writable_drink_dependency)]


async def get_drink_translation_dependency(
    drink: DrinkDependency,
    locale: LocaleDependency,
    db: DBSessionDependency,
) -> DrinkTranslation | None:
    result = await db.execute(
        select(DrinkTranslation)
        .where(DrinkTranslation.drink_id == drink.id, DrinkTranslation.locale.in_([locale, settings.default_locale]))
        .order_by(DrinkTranslation.locale != locale)
        .limit(1)
    )
    return result.scalar_one_or_none()


DrinkTranslationDependency = t.Annotated[DrinkTranslation | None, Depends(get_drink_translation_dependency)]
