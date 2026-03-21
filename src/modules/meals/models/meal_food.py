from sqlalchemy import ForeignKeyConstraint
from sqlmodel import SQLModel

from libs.models import ULIDPKField


class MealFood(SQLModel, table=True):
    __tablename__ = "meal_foods"
    __table_args__ = (ForeignKeyConstraint(["user_id", "meal_id"], ["meals.user_id", "meals.id"], ondelete="CASCADE"),)

    user_id: str = ULIDPKField()
    meal_id: str = ULIDPKField()
    food_id: str = ULIDPKField(foreign_key="foods.id")
    amount: float
