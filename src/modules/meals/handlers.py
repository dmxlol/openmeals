from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from starlette import status

from core.config import settings
from core.schemes import CursorPage
from libs.exceptions import ConflictError
from libs.pagination import PaginationDependency, paginate
from libs.types import DBSessionDependency
from modules.drinks.models import Drink
from modules.foods.models import Food
from modules.meals.dependencies import MealDependency, MealDrinkDependency, MealFoodDependency
from modules.meals.models import Meal, MealDrink, MealFood
from modules.meals.schemes import (
    MealCreate,
    MealDrinkCreate,
    MealDrinkResponse,
    MealDrinkUpdate,
    MealFoodCreate,
    MealFoodResponse,
    MealFoodUpdate,
    MealResponse,
    MealUpdate,
)
from modules.users.dependencies import CurrentUserDependency

router = APIRouter(prefix="/meals", tags=["meals"])


@router.get("", response_model=CursorPage[MealResponse])
async def list_meals(
    db: DBSessionDependency,
    user: CurrentUserDependency,
    pagination: PaginationDependency,
) -> CursorPage[Meal]:
    stmt = select(Meal).where(Meal.user_id == user.id)
    return await paginate(db, stmt, Meal, pagination)


@router.get("/{meal_id}")
async def get_meal(
    db: DBSessionDependency,
    meal: MealDependency,
) -> MealResponse:
    foods_result = await db.execute(
        select(MealFood, Food.name.label("food_name"), Food.image_key.label("food_image_key"))
        .join(Food, MealFood.food_id == Food.id)
        .where(MealFood.meal_id == meal.id, MealFood.user_id == meal.user_id)
    )
    drinks_result = await db.execute(
        select(MealDrink, Drink.name.label("drink_name"), Drink.image_key.label("drink_image_key"))
        .join(Drink, MealDrink.drink_id == Drink.id)
        .where(MealDrink.meal_id == meal.id, MealDrink.user_id == meal.user_id)
    )
    cdn = settings.s3.cdn_base_url
    foods = [
        {
            **{c.key: getattr(row.MealFood, c.key) for c in MealFood.__table__.columns},
            "food_name": row.food_name,
            "image_url": f"{cdn}/{row.food_image_key}" if row.food_image_key else None,
        }
        for row in foods_result.all()
    ]
    drinks = [
        {
            **{c.key: getattr(row.MealDrink, c.key) for c in MealDrink.__table__.columns},
            "drink_name": row.drink_name,
            "image_url": f"{cdn}/{row.drink_image_key}" if row.drink_image_key else None,
        }
        for row in drinks_result.all()
    ]
    return MealResponse.model_validate(
        {
            **{c.key: getattr(meal, c.key) for c in meal.__table__.columns},
            "foods": foods,
            "drinks": drinks,
        },
    )


@router.post("", response_model=MealResponse, status_code=status.HTTP_201_CREATED)
async def create_meal(
    body: MealCreate,
    db: DBSessionDependency,
    user: CurrentUserDependency,
) -> Meal:
    meal = Meal(**body.model_dump(), user_id=user.id)
    db.add(meal)
    await db.commit()
    await db.refresh(meal)
    return meal


@router.patch("/{meal_id}", response_model=MealResponse)
async def update_meal(
    body: MealUpdate,
    db: DBSessionDependency,
    meal: MealDependency,
) -> Meal:
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(meal, key, value)
    await db.commit()
    await db.refresh(meal)
    return meal


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal(
    db: DBSessionDependency,
    meal: MealDependency,
) -> None:
    await db.delete(meal)
    await db.commit()


# --- Meal Foods ---


@router.post("/{meal_id}/foods", status_code=status.HTTP_201_CREATED)
async def add_meal_food(
    body: MealFoodCreate,
    db: DBSessionDependency,
    meal: MealDependency,
) -> MealFoodResponse:
    meal_food = MealFood(user_id=meal.user_id, meal_id=meal.id, **body.model_dump())
    db.add(meal_food)
    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        if getattr(e.orig, "sqlstate", None) == "23505":
            raise ConflictError("Food is already in this meal") from e
        raise
    await db.refresh(meal_food)
    food = await db.get(Food, meal_food.food_id)
    cdn = settings.s3.cdn_base_url
    image_url = f"{cdn}/{food.image_key}" if food.image_key else None
    return MealFoodResponse(**meal_food.model_dump(), food_name=food.name, image_url=image_url)


@router.patch("/{meal_id}/foods/{food_id}")
async def update_meal_food(
    body: MealFoodUpdate,
    db: DBSessionDependency,
    meal_food: MealFoodDependency,
) -> MealFoodResponse:
    meal_food.amount = body.amount
    await db.commit()
    await db.refresh(meal_food)
    food = await db.get(Food, meal_food.food_id)
    cdn = settings.s3.cdn_base_url
    image_url = f"{cdn}/{food.image_key}" if food.image_key else None
    return MealFoodResponse(**meal_food.model_dump(), food_name=food.name, image_url=image_url)


@router.delete("/{meal_id}/foods/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_food(
    db: DBSessionDependency,
    meal_food: MealFoodDependency,
) -> None:
    await db.delete(meal_food)
    await db.commit()


# --- Meal Drinks ---


@router.post("/{meal_id}/drinks", status_code=status.HTTP_201_CREATED)
async def add_meal_drink(
    body: MealDrinkCreate,
    db: DBSessionDependency,
    meal: MealDependency,
) -> MealDrinkResponse:
    meal_drink = MealDrink(user_id=meal.user_id, meal_id=meal.id, **body.model_dump())
    db.add(meal_drink)
    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        if getattr(e.orig, "sqlstate", None) == "23505":
            raise ConflictError("Drink is already in this meal") from e
        raise
    await db.refresh(meal_drink)
    drink = await db.get(Drink, meal_drink.drink_id)
    cdn = settings.s3.cdn_base_url
    image_url = f"{cdn}/{drink.image_key}" if drink.image_key else None
    return MealDrinkResponse(**meal_drink.model_dump(), drink_name=drink.name, image_url=image_url)


@router.patch("/{meal_id}/drinks/{drink_id}")
async def update_meal_drink(
    body: MealDrinkUpdate,
    db: DBSessionDependency,
    meal_drink: MealDrinkDependency,
) -> MealDrinkResponse:
    meal_drink.amount = body.amount
    await db.commit()
    await db.refresh(meal_drink)
    drink = await db.get(Drink, meal_drink.drink_id)
    cdn = settings.s3.cdn_base_url
    image_url = f"{cdn}/{drink.image_key}" if drink.image_key else None
    return MealDrinkResponse(**meal_drink.model_dump(), drink_name=drink.name, image_url=image_url)


@router.delete("/{meal_id}/drinks/{drink_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_drink(
    db: DBSessionDependency,
    meal_drink: MealDrinkDependency,
) -> None:
    await db.delete(meal_drink)
    await db.commit()
