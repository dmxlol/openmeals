from httpx import AsyncClient
from starlette import status


async def test_auth_refresh(client: AsyncClient) -> None:
    response = await client.post("/auth/refresh")
    assert response.status_code == status.HTTP_200_OK
    assert "token" in response.json()
