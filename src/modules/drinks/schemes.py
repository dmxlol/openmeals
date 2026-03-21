from pydantic import Field

from libs.schemes import BaseSchema, IdSchema, NamedSchema, TimestampSchema


class DrinkBase(NamedSchema):
    ph: float
    is_carbonated: bool = False
    vitamins: dict[str, float] = Field(default_factory=dict)
    minerals: dict[str, float] = Field(default_factory=dict)
    nutrients: dict[str, float] = Field(default_factory=dict)


class DrinkCreate(DrinkBase):
    pass


class DrinkUpdate(BaseSchema):
    name: str | None = None
    ph: float | None = None
    is_carbonated: bool | None = None
    vitamins: dict[str, float] | None = None
    minerals: dict[str, float] | None = None
    nutrients: dict[str, float] | None = None


class DrinkResponse(TimestampSchema, IdSchema, DrinkBase):
    creator_id: str | None = None
    curated: bool | None = None
