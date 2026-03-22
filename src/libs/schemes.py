from pydantic import AwareDatetime, ConfigDict, Field, computed_field
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


class ImageMixin(BaseSchema):
    image_key: str | None = Field(default=None, exclude=True)
    cdn_base_url: str | None = Field(default=None, exclude=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def image_url(self) -> str | None:
        if self.image_key is None or self.cdn_base_url is None:
            return None
        return f"{self.cdn_base_url}/{self.image_key}"


class ImageUploadResponse(BaseSchema):
    upload_url: str
