from datetime import date

from sqlmodel import SQLModel

from libs.models import TimestampMixin, ULIDPKField


class UserProfile(TimestampMixin, SQLModel, table=True):
    __tablename__ = "user_profiles"

    user_id: str = ULIDPKField(foreign_key="users.id", ondelete="CASCADE")
    birthday: date
    weight: float
    height: float
