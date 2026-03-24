from sqlalchemy import Index
from sqlmodel import Field, SQLModel

from core.mixins import IngestibleMixin, IngestibleTranslationMixin
from libs.models import ULIDField


class Food(IngestibleMixin, SQLModel, table=True):
    __tablename__ = "foods"
    __table_args__ = (
        Index("ix_foods_vitamins", "vitamins", postgresql_using="gin"),
        Index("ix_foods_minerals", "minerals", postgresql_using="gin"),
        Index("ix_foods_nutrients", "nutrients", postgresql_using="gin"),
    )

    proteins: float
    carbs: float
    fats: float
    fibers: float
    sugars: float
    energy: float
    glycemic_index: float


class FoodTranslation(IngestibleTranslationMixin, SQLModel, table=True):
    __tablename__ = "food_translations"
    __table_args__ = (
        Index(
            "ix_food_translations_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    food_id: str = ULIDField(foreign_key="foods.id", primary_key=True, ondelete="CASCADE")
    locale: str = Field(primary_key=True, max_length=10)
    name: str
    description: str | None = None
