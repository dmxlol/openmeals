from libs.schemes import BaseSchema


class CursorPage[T](BaseSchema):
    items: list[T]
    total: int
    next_cursor: str | None = None
