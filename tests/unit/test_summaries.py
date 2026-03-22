from datetime import date
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status
from ulid import ULID

from libs.datetime import utcnow
from modules.summaries.dependencies import get_meal_summary_dependency, get_periodic_summary_dependency
from modules.summaries.models import MealSummary, PeriodicSummary
from modules.users.models import User


async def test_list_meal_summaries_empty(client: AsyncClient, mock_db: AsyncMock) -> None:
    count_result = MagicMock()
    count_result.scalar_one.return_value = 0
    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = []
    mock_db.execute.side_effect = [count_result, items_result]

    response = await client.get("/api/v1/meal-summaries")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


async def test_get_meal_summary(client: AsyncClient, app: FastAPI, mock_user: User) -> None:
    summary = MealSummary(
        id=str(ULID()),
        user_id=mock_user.id,
        meal_id=str(ULID()),
        computed={"calories": 500},
        model_version="v1",
        data=None,
        created=utcnow(),
        updated=utcnow(),
    )
    app.dependency_overrides[get_meal_summary_dependency] = lambda: summary

    response = await client.get(f"/api/v1/meal-summaries/{summary.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["computed"] == {"calories": 500}
    assert data["modelVersion"] == "v1"


async def test_list_periodic_summaries_empty(client: AsyncClient, mock_db: AsyncMock) -> None:
    count_result = MagicMock()
    count_result.scalar_one.return_value = 0
    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = []
    mock_db.execute.side_effect = [count_result, items_result]

    response = await client.get("/api/v1/periodic-summaries")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


async def test_get_periodic_summary(client: AsyncClient, app: FastAPI, mock_user: User) -> None:
    summary = PeriodicSummary(
        id=str(ULID()),
        user_id=mock_user.id,
        period="weekly",
        started=date(2026, 3, 16),
        computed={"avg_calories": 2000},
        model_version="v1",
        data=None,
        created=utcnow(),
        updated=utcnow(),
    )
    app.dependency_overrides[get_periodic_summary_dependency] = lambda: summary

    response = await client.get(f"/api/v1/periodic-summaries/{summary.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["period"] == "weekly"
    assert data["computed"] == {"avg_calories": 2000}


async def test_list_meal_summaries_requires_auth(anon_client: AsyncClient) -> None:
    response = await anon_client.get("/api/v1/meal-summaries")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_list_periodic_summaries_requires_auth(anon_client: AsyncClient) -> None:
    response = await anon_client.get("/api/v1/periodic-summaries")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
