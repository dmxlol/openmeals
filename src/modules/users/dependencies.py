import typing as t

from fastapi import Depends
from sqlalchemy import select

from core.config import settings
from libs.auth import JWTTokenProvider
from libs.db import fetch_one_or_raise
from libs.types import DBSessionDependency, HTTPBearerDependency
from modules.users.models import User, UserProfile

tokens = JWTTokenProvider(settings)


async def get_current_user_dependency(
    db: DBSessionDependency,
    credentials: HTTPBearerDependency,
) -> User:
    payload = tokens.decode_token(credentials.credentials, "access")
    return await fetch_one_or_raise(db, select(User).where(User.id == payload["sub"]))


async def get_current_user_profile_dependency(
    db: DBSessionDependency,
    user: t.Annotated[User, Depends(get_current_user_dependency)],
) -> UserProfile:
    return await fetch_one_or_raise(db, select(UserProfile).where(UserProfile.user_id == user.id))


CurrentUserDependency = t.Annotated[User, Depends(get_current_user_dependency)]
CurrentUserProfileDependency = t.Annotated[UserProfile, Depends(get_current_user_profile_dependency)]
