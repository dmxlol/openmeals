from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.exceptions import NotFoundError


async def fetch_one_or_raise[T](
    db: AsyncSession,
    stmt: Select[tuple[T]],
) -> T:
    result = await db.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj is None:
        entity_name = stmt.column_descriptions[0]["entity"].__name__
        raise NotFoundError(f"{entity_name} not found")
    return obj
