from pydantic import Field

from libs.schemes import BaseSchema


class CursorPage[T](BaseSchema):
    items: list[T]
    total: int = Field(description="Total number of items matching the query")
    next_cursor: str | None = Field(default=None, description="Opaque cursor for the next page, null if last")
