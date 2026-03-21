from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from core.config import settings
from libs.models import TimestampMixin, ULIDField, ULIDPKMixin


class IngestibleMixin(ULIDPKMixin, TimestampMixin, SQLModel):
    name: str
    vitamins: dict = Field(sa_type=JSONB, default_factory=dict)
    minerals: dict = Field(sa_type=JSONB, default_factory=dict)
    nutrients: dict = Field(sa_type=JSONB, default_factory=dict)
    creator_id: str | None = ULIDField(default=None)
    curated: bool | None = None
    embedding: list[float] | None = Field(default=None, sa_type=Vector(settings.embedding.dimension))
