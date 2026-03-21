from datetime import date

from libs.schemes import IdSchema, TimestampSchema
from libs.types import ULIDStr


class MealSummaryResponse(TimestampSchema, IdSchema):
    user_id: ULIDStr
    meal_id: ULIDStr
    computed: dict
    model_version: str
    data: str | None = None


class PeriodicSummaryResponse(TimestampSchema, IdSchema):
    user_id: ULIDStr
    period: str  # todo: enum
    started: date
    computed: dict
    model_version: str  # todo: enum
    data: str | None = None
