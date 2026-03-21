import typing as t

from sqlalchemy import Select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from libs.exceptions import ForbiddenError, NotFoundError
from libs.models import ULIDPKMixin

if t.TYPE_CHECKING:
    from core.mixins import IngestibleMixin


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


# Ingestible visibility rules (foods/drinks):
#   - creator_id is None → global (seeded/imported), visible to all
#   - creator_id == user_id → user's own, visible to creator
#   - curated is True → admin-approved, visible to all
# Write (update/delete) is only allowed for user's own non-curated items.


def ingestible_visible_filter(model: type["IngestibleMixin"], user: ULIDPKMixin | None = None):
    """WHERE clause: ingestible items the user is allowed to see.

    Anonymous: global (creator_id is None) + curated.
    Authenticated: global + curated + user's own.
    """
    public = or_(model.creator_id.is_(None), model.curated.is_(True))
    if user is None:
        return public
    return or_(public, model.creator_id == user.id)


def check_ingestible_writable(item: "IngestibleMixin", user: ULIDPKMixin) -> None:
    """Raise ForbiddenError if the user cannot modify this ingestible."""
    if item.creator_id != user.id or item.curated is True:
        raise ForbiddenError
