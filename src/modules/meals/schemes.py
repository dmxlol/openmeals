from pydantic import Field

from libs.schemes import BaseSchema, NamedIdSchema, NamedSchema, TimestampSchema
from libs.types import ULIDStr


class MealCreate(NamedSchema):
    pass


class MealUpdate(BaseSchema):
    name: str | None = None


class MealResponse(TimestampSchema, NamedIdSchema):
    user_id: ULIDStr
    foods: list["MealFoodResponse"] = []
    drinks: list["MealDrinkResponse"] = []


class MealFoodCreate(BaseSchema):
    food_id: ULIDStr
    amount: float = Field(description="Amount in grams")


class MealFoodUpdate(BaseSchema):
    amount: float = Field(description="Amount in grams")


class MealFoodResponse(BaseSchema):
    user_id: ULIDStr
    meal_id: ULIDStr
    food_id: ULIDStr
    food_name: str
    image_url: str | None = None
    amount: float = Field(description="Amount in grams")


class MealDrinkCreate(BaseSchema):
    drink_id: ULIDStr
    amount: float = Field(description="Amount in milliliters")


class MealDrinkUpdate(BaseSchema):
    amount: float = Field(description="Amount in milliliters")


class MealDrinkResponse(BaseSchema):
    user_id: ULIDStr
    meal_id: ULIDStr
    drink_id: ULIDStr
    drink_name: str
    image_url: str | None = None
    amount: float = Field(description="Amount in milliliters")
