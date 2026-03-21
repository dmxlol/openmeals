from pydantic import AwareDatetime
from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel

from libs.datetime import utcnow
from libs.models import ULIDPKMixin


class User(ULIDPKMixin, SQLModel, table=True):
    __tablename__ = "users"

    created: AwareDatetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=utcnow,
    )
