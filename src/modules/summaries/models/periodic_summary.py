from datetime import date

from sqlalchemy import Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from libs.models import TimestampMixin, ULIDPKField, ULIDPKMixin


class PeriodicSummary(TimestampMixin, ULIDPKMixin, SQLModel, table=True):
    __tablename__ = "periodic_summaries"
    __table_args__ = (
        UniqueConstraint("user_id", "period", "started", name="uq_periodic_summaries_user_period_started"),
    )

    user_id: str = ULIDPKField(foreign_key="users.id", ondelete="CASCADE")
    period: str
    started: date
    computed: dict = Field(sa_type=JSONB)
    model_version: str | None = Field(default=None, sa_type=Text)
    data: str | None = Field(default=None, sa_type=Text)
