from pydantic import AwareDatetime
from sqlalchemy import DateTime, Index
from sqlmodel import Field, SQLModel

from libs.datetime import utcnow
from libs.models import ULIDField


class UserOAuth(SQLModel, table=True):
    __tablename__ = "user_oauth"
    __table_args__ = (Index("ix_user_oauth_user_id", "user_id"),)

    provider: str = Field(primary_key=True)
    sub: str = Field(primary_key=True)
    user_id: str = ULIDField(foreign_key="users.id", ondelete="CASCADE")
    email: str
    created: AwareDatetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=utcnow,
    )
