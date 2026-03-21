from fastapi import APIRouter
from starlette import status

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/{provider}")
async def oauth_redirect(provider: str) -> dict[str, str]:
    # TODO: implement OAuth redirect
    return {"redirect": f"/auth/{provider}"}


@router.get("/{provider}/callback")
async def oauth_callback(provider: str) -> dict[str, str]:
    # TODO: implement OAuth callback, issue JWT
    return {"token": "stub"}


@router.post("/refresh")
async def refresh_token() -> dict[str, str]:
    # TODO: implement token refresh
    return {"token": "stub"}


@router.delete("/session", status_code=status.HTTP_204_NO_CONTENT)
async def logout() -> None:
    # TODO: implement logout
    pass
