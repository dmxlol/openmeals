from sqlalchemy import Index
from sqlmodel import SQLModel

from core.mixins import IngestibleMixin


class Food(IngestibleMixin, SQLModel, table=True):
    __tablename__ = "foods"
    __table_args__ = (
        Index("ix_foods_vitamins", "vitamins", postgresql_using="gin"),
        Index("ix_foods_minerals", "minerals", postgresql_using="gin"),
        Index("ix_foods_nutrients", "nutrients", postgresql_using="gin"),
        Index(
            "ix_foods_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    proteins: float
    carbs: float
    fats: float
    fibers: float
    sugars: float
    energy: float
    glycemic_index: float
