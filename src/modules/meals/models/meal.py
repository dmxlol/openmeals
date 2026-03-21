from sqlmodel import SQLModel

from libs.models import TimestampMixin, ULIDPKField, ULIDPKMixin


class Meal(TimestampMixin, ULIDPKMixin, SQLModel, table=True):
    __tablename__ = "meals"

    user_id: str = ULIDPKField(
        foreign_key="users.id",
        ondelete="CASCADE",
    )
    name: str
