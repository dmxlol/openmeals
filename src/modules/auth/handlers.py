import typing as t

from fastapi import APIRouter, Query
from sqlalchemy import select
from starlette import status

from core.config import settings
from libs.auth import JWTTokenProvider, get_provider
from libs.auth.providers import OAuthProviderName
from libs.exceptions import UnauthorizedError
from libs.types import DBSessionDependency
from modules.auth.models import UserOAuth
from modules.auth.schemes import RefreshRequest, TokenResponse
from modules.users.models import User

router = APIRouter(prefix="/auth", tags=["auth"])
tokens = JWTTokenProvider(settings)


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: OAuthProviderName,
    db: DBSessionDependency,
    code: t.Annotated[str, Query()],
) -> TokenResponse:
    oauth_provider = get_provider(provider)
    claims = oauth_provider.decode(code, settings)

    result = await db.execute(
        select(UserOAuth).where(UserOAuth.provider == provider.value, UserOAuth.sub == claims["sub"])
    )
    user_oauth = result.scalar_one_or_none()

    if user_oauth is None:
        user = User(name=claims["name"])
        db.add(user)
        await db.flush()

        user_oauth = UserOAuth(
            provider=provider.value,
            sub=claims["sub"],
            user_id=user.id,
            email=claims["email"],
        )
        db.add(user_oauth)
        await db.commit()
    else:
        user = await db.get(User, user_oauth.user_id)

    return TokenResponse(**tokens.create_token_pair(user.id, user.name))


@router.post("/refresh")
async def refresh_token(body: RefreshRequest, db: DBSessionDependency) -> TokenResponse:
    payload = tokens.decode_token(body.refresh_token, "refresh")
    user = await db.get(User, payload["sub"])
    if user is None:
        raise UnauthorizedError
    return TokenResponse(**tokens.create_token_pair(user.id, user.name))


@router.delete("/session", status_code=status.HTTP_204_NO_CONTENT)
async def logout() -> None:
    pass
