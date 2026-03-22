import typing as t

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BeforeValidator, PlainSerializer
from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID

from core.config import settings
from core.database import get_db_dependency
from libs.s3 import get_s3_resource

if t.TYPE_CHECKING:
    from mypy_boto3_s3.service_resource import Bucket


def get_s3_bucket_dependency() -> "Bucket":
    return get_s3_resource().Bucket(settings.s3.bucket)


ULIDStr = t.Annotated[ULID, BeforeValidator(ULID.from_str), PlainSerializer(str, return_type=str)]
DBSessionDependency = t.Annotated[AsyncSession, Depends(get_db_dependency)]
S3BucketDependency = t.Annotated["Bucket", Depends(get_s3_bucket_dependency)]
HTTPBearerDependency = t.Annotated[HTTPAuthorizationCredentials, Security(HTTPBearer())]
OptionalHTTPBearerDependency = t.Annotated[HTTPAuthorizationCredentials | None, Security(HTTPBearer(auto_error=False))]
