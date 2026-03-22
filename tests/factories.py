from pgvector.sqlalchemy import Vector
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from libs.datetime import utcnow
from libs.models import generate_ulid
from modules.drinks.models import Drink
from modules.foods.models import Food
from modules.meals.models import Meal, MealDrink, MealFood
from modules.users.models import User


class _BaseFactory(SQLAlchemyFactory):
    __is_base_factory__ = True

    @classmethod
    def get_sqlalchemy_types(cls):
        return {**super().get_sqlalchemy_types(), Vector: lambda: None}

    id = generate_ulid
    created = utcnow
    updated = utcnow


class UserFactory(_BaseFactory):
    __model__ = User


class FoodFactory(_BaseFactory):
    __model__ = Food

    embedding = None
    creator_id = None
    curated = None
    vitamins = {}
    minerals = {}
    nutrients = {}


class DrinkFactory(_BaseFactory):
    __model__ = Drink

    embedding = None
    creator_id = None
    curated = None
    vitamins = {}
    minerals = {}
    nutrients = {}


class MealFactory(_BaseFactory):
    __model__ = Meal


class MealFoodFactory(_BaseFactory):
    __model__ = MealFood


class MealDrinkFactory(_BaseFactory):
    __model__ = MealDrink
