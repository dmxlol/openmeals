from fastapi import APIRouter
from sqlalchemy import select
from starlette import status

from libs.types import DBSessionDependency
from modules.users.dependencies import CurrentUserDependency, CurrentUserProfileDependency
from modules.users.models import User, UserProfile
from modules.users.schemes import UserProfileResponse, UserProfileUpdate, UserResponse
from utils.fastapi import RESPONSES_AUTH, RESPONSES_NOT_FOUND, merge_responses

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse, summary="Get the current user", responses=RESPONSES_AUTH)
async def get_me(
    user: CurrentUserDependency,
) -> User:
    return user


@router.delete(
    "/me", status_code=status.HTTP_204_NO_CONTENT, summary="Delete the current user", responses=RESPONSES_AUTH
)
async def delete_me(
    db: DBSessionDependency,
    user: CurrentUserDependency,
) -> None:
    await db.delete(user)
    await db.commit()


@router.get(
    "/me/profile",
    response_model=UserProfileResponse,
    summary="Get the current user's profile",
    responses=merge_responses(RESPONSES_AUTH, RESPONSES_NOT_FOUND),
)
async def get_my_profile(
    profile: CurrentUserProfileDependency,
) -> UserProfile:
    return profile


@router.put(
    "/me/profile",
    response_model=UserProfileResponse,
    summary="Create or replace the user profile",
    responses=RESPONSES_AUTH,
)
async def upsert_my_profile(
    body: UserProfileUpdate,
    db: DBSessionDependency,
    user: CurrentUserDependency,
) -> UserProfile:
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = UserProfile(user_id=user.id, **body.model_dump())
        db.add(profile)
    else:
        for key, value in body.model_dump().items():
            setattr(profile, key, value)
    await db.commit()
    await db.refresh(profile)
    return profile
