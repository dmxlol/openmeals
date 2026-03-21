from pydantic import AwareDatetime, ConfigDict, TypeAdapter
from pydantic import BaseModel as PydanticModel
from pydantic.alias_generators import to_camel

from .types import ULIDStr


class BaseSchema(PydanticModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class IdSchema(BaseSchema):
    id: ULIDStr


class NamedSchema(BaseSchema):
    name: str  # todo define common name rules ?


class NamedIdSchema(IdSchema, NamedSchema, BaseSchema):
    pass


class UpdatedSchema(BaseSchema):
    updated: AwareDatetime


class CreatedSchema(BaseSchema):
    created: AwareDatetime


class TimestampSchema(UpdatedSchema, CreatedSchema):
    pass


class UserIdSchema(BaseSchema):
    user_id: ULIDStr


class SearchResultSchema(NamedIdSchema):
    score: float


SearchResultList = TypeAdapter(list[SearchResultSchema])
