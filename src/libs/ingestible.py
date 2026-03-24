import typing as t
from collections.abc import Callable, Coroutine

from sqlalchemy import select
from sqlalchemy.orm import InstrumentedAttribute
from sqlmodel import SQLModel

from core.config import settings
from libs.db import check_ingestible_writable, fetch_one_or_raise, ingestible_visible_filter
from libs.types import DBSessionDependency, ULIDStr


def make_get_dependency[T: SQLModel](
    model: type[T],
    user_dep: t.Annotated[t.Any, t.Any],
) -> Callable[..., Coroutine[t.Any, t.Any, T]]:
    async def get(pk: ULIDStr, db: DBSessionDependency, user: user_dep) -> T:
        return await fetch_one_or_raise(db, select(model).where(model.id == pk, ingestible_visible_filter(model, user)))

    return get


def make_get_writable_dependency[T: SQLModel](
    model: type[T],
    user_dep: t.Annotated[t.Any, t.Any],
) -> Callable[..., Coroutine[t.Any, t.Any, T]]:
    async def get_writable(pk: ULIDStr, db: DBSessionDependency, user: user_dep) -> T:
        entity = await fetch_one_or_raise(db, select(model).where(model.id == pk))
        check_ingestible_writable(entity, user)
        return entity

    return get_writable


def make_get_translation_dependency[Tr: SQLModel](
    entity_dep: t.Annotated[t.Any, t.Any],
    translation_model: type[Tr],
    id_col: InstrumentedAttribute,
    locale_dep: t.Annotated[t.Any, t.Any],
) -> Callable[..., Coroutine[t.Any, t.Any, Tr | None]]:
    async def get_translation(entity: entity_dep, locale: locale_dep, db: DBSessionDependency) -> Tr | None:
        result = await db.execute(
            select(translation_model)
            .where(id_col == entity.id, translation_model.locale.in_([locale, settings.default_locale]))
            .order_by(translation_model.locale != locale)
            .limit(1)
        )
        return result.scalar_one_or_none()

    return get_translation
