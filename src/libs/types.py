import typing as t

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BeforeValidator
from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID

from core.database import get_db_dependency

ULIDStr = t.Annotated[ULID, BeforeValidator(ULID.from_str)]
DBSessionDependency = t.Annotated[AsyncSession, Depends(get_db_dependency)]
HTTPBearerDependency = t.Annotated[HTTPAuthorizationCredentials, Security(HTTPBearer())]
