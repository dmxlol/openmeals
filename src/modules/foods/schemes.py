from pydantic import Field

from core.config import settings
from libs.schemes import BaseSchema, IdSchema, ImageMixin, NamedSchema, TimestampSchema
from libs.types import ULIDStr


class FoodBase(NamedSchema):
    proteins: float = Field(description="Grams per 100g")
    carbs: float = Field(description="Grams per 100g")
    fats: float = Field(description="Grams per 100g")
    fibers: float = Field(description="Grams per 100g")
    sugars: float = Field(description="Grams per 100g")
    energy: float = Field(description="Energy in kcal per 100g")
    glycemic_index: float = Field(description="Glycemic index (0–100)")
    vitamins: dict[str, float] = Field(default_factory=dict, description="Vitamin amounts in mg per 100g")
    minerals: dict[str, float] = Field(default_factory=dict, description="Mineral amounts in mg per 100g")
    nutrients: dict[str, float] = Field(default_factory=dict, description="Additional nutrient amounts per 100g")


class FoodCreate(FoodBase):
    pass


class FoodUpdate(BaseSchema):
    name: str | None = None
    proteins: float | None = None
    carbs: float | None = None
    fats: float | None = None
    fibers: float | None = None
    sugars: float | None = None
    energy: float | None = None
    glycemic_index: float | None = None
    vitamins: dict[str, float] | None = None
    minerals: dict[str, float] | None = None
    nutrients: dict[str, float] | None = None


class FoodResponse(ImageMixin, TimestampSchema, IdSchema, FoodBase):
    cdn_base_url: str = Field(default=settings.s3.cdn_base_url, exclude=True)
    creator_id: ULIDStr | None = None
    curated: bool | None = None
    description: str | None = None


class FoodSearchResult(FoodResponse):
    score: float = Field(description="Cosine distance to query (lower = more relevant)")
