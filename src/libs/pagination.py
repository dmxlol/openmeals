import typing as t

from fastapi import Depends
from pydantic import Field
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.schemes import CursorPage
from libs.models import ULIDPKMixin
from libs.schemes import BaseSchema


class PaginationParams(BaseSchema):
    cursor: str | None = Field(default=None, description="Cursor from a previous response's nextCursor")
    limit: t.Annotated[int, Field(ge=1, le=100, description="Maximum items to return")] = 20


PaginationDependency = t.Annotated[PaginationParams, Depends(PaginationParams)]


async def paginate[T: ULIDPKMixin](
    db: AsyncSession,
    stmt: Select[tuple[T]],
    model: type[T],
    params: PaginationParams,
) -> CursorPage[T]:
    """Apply cursor-based pagination to a SELECT statement.

    Expects `stmt` without ORDER BY — ordering by `model.id` (ULID) is added here.
    Fetches limit+1 rows to determine if a next page exists.
    """
    count_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_result.scalar_one()

    if params.cursor is not None:
        stmt = stmt.where(model.id > params.cursor)
    stmt = stmt.order_by(model.id).limit(params.limit + 1)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    next_cursor = None
    if len(items) > params.limit:
        items = items[: params.limit]
        next_cursor = items[-1].id

    return CursorPage(items=items, total=total, next_cursor=next_cursor)
