from sqlalchemy import Index
from sqlmodel import Field, SQLModel

from core.mixins import IngestibleMixin, IngestibleTranslationMixin
from libs.models import ULIDField


class Drink(IngestibleMixin, SQLModel, table=True):
    __tablename__ = "drinks"
    __table_args__ = (
        Index("ix_drinks_vitamins", "vitamins", postgresql_using="gin"),
        Index("ix_drinks_minerals", "minerals", postgresql_using="gin"),
        Index("ix_drinks_nutrients", "nutrients", postgresql_using="gin"),
    )

    ph: float
    is_carbonated: bool = False


class DrinkTranslation(IngestibleTranslationMixin, SQLModel, table=True):
    __tablename__ = "drink_translations"
    __table_args__ = (
        Index(
            "ix_drink_translations_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    drink_id: str = ULIDField(foreign_key="drinks.id", primary_key=True, ondelete="CASCADE")
    locale: str = Field(primary_key=True, max_length=10)
    name: str
    description: str | None = None
