import typing as t

from fastapi import Depends
from sqlalchemy import select

from libs.db import fetch_one_or_raise
from libs.types import DBSessionDependency
from modules.users.models import User, UserProfile


async def get_current_user_dependency(
    db: DBSessionDependency,
) -> User:
    # TODO: resolve current user from JWT
    return await fetch_one_or_raise(db, select(User).limit(1))


async def get_current_user_profile_dependency(
    db: DBSessionDependency,
) -> UserProfile:
    # TODO: resolve current user from JWT
    return await fetch_one_or_raise(db, select(UserProfile).limit(1))


CurrentUserDependency = t.Annotated[User, Depends(get_current_user_dependency)]
CurrentUserProfileDependency = t.Annotated[UserProfile, Depends(get_current_user_profile_dependency)]
