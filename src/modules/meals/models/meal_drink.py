from sqlalchemy import ForeignKeyConstraint
from sqlmodel import SQLModel

from libs.models import ULIDPKField


class MealDrink(SQLModel, table=True):
    __tablename__ = "meal_drinks"
    __table_args__ = (ForeignKeyConstraint(["user_id", "meal_id"], ["meals.user_id", "meals.id"], ondelete="CASCADE"),)

    user_id: str = ULIDPKField()
    meal_id: str = ULIDPKField()
    drink_id: str = ULIDPKField(foreign_key="drinks.id")
    amount: float
