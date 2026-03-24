from datetime import date

from core.config import settings
from libs.locale import Locale
from libs.schemes import BaseSchema, CreatedSchema, IdSchema, TimestampSchema
from libs.types import ULIDStr


class UserResponse(IdSchema, CreatedSchema):
    name: str


class UserProfileBase(BaseSchema):
    birthday: date
    weight: float
    height: float
    locale: Locale = Locale(settings.default_locale)


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileResponse(TimestampSchema, UserProfileBase):
    user_id: ULIDStr
