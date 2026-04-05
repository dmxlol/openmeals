from datetime import date
from enum import StrEnum

from pydantic import Field

from libs.schemes import IdSchema, TimestampSchema
from libs.types import ULIDStr


class SummaryPeriod(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class MealSummaryResponse(TimestampSchema, IdSchema):
    user_id: ULIDStr
    meal_id: ULIDStr
    computed: dict = Field(description="AI-computed nutritional analysis")
    model_version: str = Field(description="Version of the AI model used")
    data: str | None = Field(default=None, description="Raw LLM output text")


class PeriodicSummaryResponse(TimestampSchema, IdSchema):
    user_id: ULIDStr
    period: SummaryPeriod
    started: date
    computed: dict = Field(description="AI-computed nutritional analysis")
    model_version: str = Field(description="Version of the AI model used")
    data: str | None = Field(default=None, description="Raw LLM output text")
