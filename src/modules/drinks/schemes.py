from pydantic import Field

from core.config import settings
from libs.schemes import BaseSchema, IdSchema, ImageMixin, NamedSchema, TimestampSchema
from libs.types import ULIDStr


class DrinkBase(NamedSchema):
    ph: float = Field(description="pH level (0–14)")
    is_carbonated: bool = False
    vitamins: dict[str, float] = Field(default_factory=dict, description="Vitamin amounts in mg per 100ml")
    minerals: dict[str, float] = Field(default_factory=dict, description="Mineral amounts in mg per 100ml")
    nutrients: dict[str, float] = Field(default_factory=dict, description="Additional nutrient amounts per 100ml")


class DrinkCreate(DrinkBase):
    pass


class DrinkUpdate(BaseSchema):
    name: str | None = None
    ph: float | None = None
    is_carbonated: bool | None = None
    vitamins: dict[str, float] | None = None
    minerals: dict[str, float] | None = None
    nutrients: dict[str, float] | None = None


class DrinkResponse(ImageMixin, TimestampSchema, IdSchema, DrinkBase):
    cdn_base_url: str = Field(default=settings.s3.cdn_base_url, exclude=True)
    creator_id: ULIDStr | None = None
    curated: bool | None = None
    description: str | None = None


class DrinkSearchResult(DrinkResponse):
    score: float = Field(description="Cosine distance to query (lower = more relevant)")
