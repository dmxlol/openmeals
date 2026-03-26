import typing as t

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from core.config import settings
from libs.locale import Locale


async def fetch_translations(
    db: AsyncSession,
    model: type[SQLModel],
    id_col: t.Any,
    ids: list[str],
    locale: Locale,
) -> dict[str, t.Any]:
    if not ids:
        return {}
    default_locale = settings.default_locale
    result = await db.execute(
        select(model)
        .where(id_col.in_(ids), model.locale.in_([locale, default_locale]))
        .distinct(id_col)
        .order_by(id_col, model.locale != locale)
    )
    return {getattr(tr, id_col.key): tr for tr in result.scalars()}


async def batch_names(
    db: AsyncSession,
    model: type[SQLModel],
    id_col: t.Any,
    ids: list[str],
    locale: Locale,
) -> dict[str, str]:
    """Resolve display names for a list of entity IDs with locale fallback."""
    if not ids:
        return {}
    result = await db.execute(
        select(id_col, model.name)
        .where(id_col.in_(ids), model.locale.in_([locale, settings.default_locale]))
        .distinct(id_col)
        .order_by(id_col, model.locale != locale)
    )
    return dict(result.all())


def apply_translation[T](entity: t.Any, translation: t.Any | None, schema: type[T]) -> T:
    data = entity.model_dump(mode="json")
    if translation is not None:
        data["name"] = translation.name
        if translation.description is not None:
            data["description"] = translation.description
    return schema.model_validate(data)
