from fastapi import APIRouter
from starlette import status

from libs.types import DBSessionDependency
from modules.users.dependencies import CurrentUserDependency, CurrentUserProfileDependency
from modules.users.models import User, UserProfile
from modules.users.schemes import UserProfileResponse, UserProfileUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: CurrentUserDependency,
) -> User:
    return user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    db: DBSessionDependency,
    user: CurrentUserDependency,
) -> None:
    await db.delete(user)
    await db.commit()


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_my_profile(
    profile: CurrentUserProfileDependency,
) -> UserProfile:
    return profile


@router.patch("/me/profile", response_model=UserProfileResponse)
async def update_my_profile(
    body: UserProfileUpdate,
    db: DBSessionDependency,
    profile: CurrentUserProfileDependency,
) -> UserProfile:
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    await db.commit()
    await db.refresh(profile)
    return profile
