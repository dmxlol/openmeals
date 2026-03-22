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
    amount: float


class MealFoodUpdate(BaseSchema):
    amount: float


class MealFoodResponse(BaseSchema):
    user_id: ULIDStr
    meal_id: ULIDStr
    food_id: ULIDStr
    food_name: str
    image_url: str | None = None
    amount: float


class MealDrinkCreate(BaseSchema):
    drink_id: str
    amount: float


class MealDrinkUpdate(BaseSchema):
    amount: float


class MealDrinkResponse(BaseSchema):
    user_id: str
    meal_id: str
    drink_id: str
    drink_name: str
    image_url: str | None = None
    amount: float
