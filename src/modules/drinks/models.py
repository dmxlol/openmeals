from sqlalchemy import Index
from sqlmodel import Field, SQLModel

from core.config import settings
from core.mixins import IngestibleMixin


class Drink(IngestibleMixin, SQLModel, table=True):
    __tablename__ = "drinks"
    image_key: str = Field(default=settings.s3.default_drink_image_key, max_length=512)
    __table_args__ = (
        Index("ix_drinks_vitamins", "vitamins", postgresql_using="gin"),
        Index("ix_drinks_minerals", "minerals", postgresql_using="gin"),
        Index("ix_drinks_nutrients", "nutrients", postgresql_using="gin"),
        Index(
            "ix_drinks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    ph: float
    is_carbonated: bool = False
