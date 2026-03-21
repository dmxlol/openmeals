from datetime import datetime
from functools import partial

from sqlalchemy import DateTime, String, func
from sqlmodel import Field, SQLModel
from ulid import ULID

from libs.datetime import utcnow


def generate_ulid() -> str:
    return str(ULID())


ULIDField = partial(Field, max_length=26, sa_type=String(26))

ULIDPKField = partial(ULIDField, primary_key=True)


class ULIDPKMixin(SQLModel):
    id: str = ULIDPKField(
        default_factory=generate_ulid,
    )


class TimestampMixin(SQLModel):
    created: datetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=utcnow,
    )
    updated: datetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=utcnow,
        sa_column_kwargs={"onupdate": func.now()},
    )
