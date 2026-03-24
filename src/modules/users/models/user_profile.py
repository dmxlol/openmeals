from datetime import date

from sqlmodel import Field, SQLModel

from core.config import settings
from libs.models import TimestampMixin, ULIDPKField


class UserProfile(TimestampMixin, SQLModel, table=True):
    __tablename__ = "user_profiles"

    user_id: str = ULIDPKField(foreign_key="users.id", ondelete="CASCADE")
    birthday: date
    weight: float
    height: float
    locale: str = Field(default=settings.default_locale, max_length=10)
