import typing as t

from fastapi import Depends
from sqlalchemy import select

from libs.db import fetch_one_or_raise
from libs.types import DBSessionDependency
from modules.summaries.models import MealSummary, PeriodicSummary
from modules.users.dependencies import CurrentUserDependency


async def get_meal_summary_dependency(
    summary_id: str,
    db: DBSessionDependency,
    user: CurrentUserDependency,
) -> MealSummary:
    return await fetch_one_or_raise(
        db, select(MealSummary).where(MealSummary.id == summary_id, MealSummary.user_id == user.id)
    )


async def get_periodic_summary_dependency(
    summary_id: str,
    db: DBSessionDependency,
    user: CurrentUserDependency,
) -> PeriodicSummary:
    return await fetch_one_or_raise(
        db, select(PeriodicSummary).where(PeriodicSummary.id == summary_id, PeriodicSummary.user_id == user.id)
    )


MealSummaryDependency = t.Annotated[MealSummary, Depends(get_meal_summary_dependency)]
PeriodicSummaryDependency = t.Annotated[PeriodicSummary, Depends(get_periodic_summary_dependency)]
