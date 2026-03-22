import typing as t

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BeforeValidator, WithJsonSchema
from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID

from core.config import settings
from core.database import get_db_dependency
from libs.s3 import get_s3_resource

if t.TYPE_CHECKING:
    from mypy_boto3_s3.service_resource import Bucket


def get_s3_bucket_dependency() -> "Bucket":
    return get_s3_resource().Bucket(settings.s3.bucket)


def parse_ulid(v: object) -> str:
    if isinstance(v, ULID):
        return str(v)
    s = str(v)
    ULID.from_str(s)  # validates format, raises ValueError on invalid input
    return s


ULIDStr = t.Annotated[
    str,
    BeforeValidator(parse_ulid),
    WithJsonSchema(
        {
            "type": "string",
            "pattern": r"^[0-9A-HJKMNP-TV-Za-hjkmnp-tv-z]{26}$",
            "minLength": 26,
            "maxLength": 26,
            "example": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
        }
    ),
]
DBSessionDependency = t.Annotated[AsyncSession, Depends(get_db_dependency)]
S3BucketDependency = t.Annotated["Bucket", Depends(get_s3_bucket_dependency)]
HTTPBearerDependency = t.Annotated[HTTPAuthorizationCredentials, Security(HTTPBearer())]
OptionalHTTPBearerDependency = t.Annotated[HTTPAuthorizationCredentials | None, Security(HTTPBearer(auto_error=False))]
