from fastapi import APIRouter
from sqlalchemy import select

from libs.types import DBSessionDependency
from modules.summaries.dependencies import (
    MealSummaryDependency,
    PeriodicSummaryDependency,
)
from modules.summaries.models import MealSummary, PeriodicSummary
from modules.summaries.schemes import MealSummaryResponse, PeriodicSummaryResponse

router = APIRouter(tags=["summaries"])


@router.get("/meal-summaries", response_model=list[MealSummaryResponse])
async def list_meal_summaries(
    db: DBSessionDependency,
) -> list[MealSummary]:
    # TODO: filter by current user
    result = await db.execute(select(MealSummary))
    return list(result.scalars().all())


@router.get("/meal-summaries/{summary_id}", response_model=MealSummaryResponse)
async def get_meal_summary(
    summary: MealSummaryDependency,
) -> MealSummary:
    return summary


@router.get("/periodic-summaries", response_model=list[PeriodicSummaryResponse])
async def list_periodic_summaries(
    db: DBSessionDependency,
) -> list[PeriodicSummary]:
    # TODO: filter by current user
    result = await db.execute(select(PeriodicSummary))
    return list(result.scalars().all())


@router.get("/periodic-summaries/{summary_id}", response_model=PeriodicSummaryResponse)
async def get_periodic_summary(
    summary: PeriodicSummaryDependency,
) -> PeriodicSummary:
    return summary
