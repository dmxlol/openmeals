from pydantic import Field

from core.config import settings
from libs.schemes import BaseSchema, IdSchema, ImageMixin, NamedSchema, TimestampSchema
from libs.types import ULIDStr


class FoodBase(NamedSchema):
    proteins: float
    carbs: float
    fats: float
    fibers: float
    sugars: float
    energy: float
    glycemic_index: float
    vitamins: dict[str, float] = Field(default_factory=dict)
    minerals: dict[str, float] = Field(default_factory=dict)
    nutrients: dict[str, float] = Field(default_factory=dict)


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
    score: float
