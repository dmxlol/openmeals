import typing as t

from fastapi import Depends, Request
from sqlalchemy import select

from core.config import settings
from libs.auth import JWTTokenProvider
from libs.db import fetch_one_or_raise
from libs.locale import Locale
from libs.types import DBSessionDependency, HTTPBearerDependency, OptionalHTTPBearerDependency
from modules.users.models import User, UserProfile
from services.locale import accept_language_parser

tokens = JWTTokenProvider(settings)


async def get_current_user_dependency(
    db: DBSessionDependency,
    credentials: HTTPBearerDependency,
) -> User:
    payload = tokens.decode_token(credentials.credentials, "access")
    return await fetch_one_or_raise(db, select(User).where(User.id == payload["sub"]))


async def get_optional_user_dependency(
    db: DBSessionDependency,
    credentials: OptionalHTTPBearerDependency,
) -> User | None:
    if credentials is None:
        return None
    payload = tokens.decode_token(credentials.credentials, "access")
    result = await db.execute(select(User).where(User.id == payload["sub"]))
    return result.scalar_one_or_none()


CurrentUserDependency = t.Annotated[User, Depends(get_current_user_dependency)]
OptionalUserDependency = t.Annotated[User | None, Depends(get_optional_user_dependency)]


async def get_current_user_profile_dependency(
    db: DBSessionDependency,
    user: CurrentUserDependency,
) -> UserProfile:
    return await fetch_one_or_raise(db, select(UserProfile).where(UserProfile.user_id == user.id))


async def get_locale_dependency(
    request: Request,
    db: DBSessionDependency,
    user: OptionalUserDependency,
) -> Locale:
    if user is not None:
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
        profile = result.scalar_one_or_none()
        if profile is not None:
            try:
                return Locale(profile.locale)
            except ValueError:
                pass
    accept_lang = request.headers.get("Accept-Language")
    if accept_lang:
        return accept_language_parser(accept_lang)
    return Locale(settings.default_locale)


CurrentUserProfileDependency = t.Annotated[UserProfile, Depends(get_current_user_profile_dependency)]
LocaleDependency = t.Annotated[Locale, Depends(get_locale_dependency)]
