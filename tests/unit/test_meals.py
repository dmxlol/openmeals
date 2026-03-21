from unittest.mock import AsyncMock, MagicMock

from httpx import AsyncClient
from starlette import status


async def test_list_meals(client: AsyncClient, mock_db: AsyncMock) -> None:
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    response = await client.get("/meals/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []
