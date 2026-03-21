from sqlalchemy import ForeignKeyConstraint, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from libs.models import TimestampMixin, ULIDField, ULIDPKField, ULIDPKMixin


class MealSummary(TimestampMixin, ULIDPKMixin, SQLModel, table=True):
    __tablename__ = "meal_summaries"
    __table_args__ = (ForeignKeyConstraint(["user_id", "meal_id"], ["meals.user_id", "meals.id"], ondelete="CASCADE"),)

    user_id: str = ULIDPKField()

    meal_id: str = ULIDField()
    computed: dict = Field(sa_type=JSONB)
    model_version: str | None = Field(default=None, sa_type=String)
    data: str | None = Field(default=None, sa_type=Text)
