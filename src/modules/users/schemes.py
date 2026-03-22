from datetime import date

from libs.schemes import BaseSchema, CreatedSchema, IdSchema, TimestampSchema
from libs.types import ULIDStr


class UserResponse(IdSchema, CreatedSchema):
    name: str


class UserProfileBase(BaseSchema):
    birthday: date
    weight: float
    height: float


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileResponse(TimestampSchema, UserProfileBase):
    user_id: ULIDStr
