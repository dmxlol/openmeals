from fastapi import APIRouter, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from starlette import status

from core.config import settings
from core.schemes import CursorPage
from libs.exceptions import ConflictError
from libs.pagination import PaginationDependency, paginate
from libs.translations import batch_names, fetch_translations
from libs.types import DBSessionDependency
from modules.drinks.models import Drink, DrinkTranslation
from modules.foods.models import Food, FoodTranslation
from modules.meals.dependencies import (
    MealDependency,
    MealDrinkDependency,
    MealDrinkTranslationDependency,
    MealFoodDependency,
    MealFoodTranslationDependency,
)
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
from modules.users.dependencies import CurrentUserDependency, LocaleDependency
from services.ratelimit import brand_limit, limiter, user_limit_strategy

router = APIRouter(prefix="/meals", tags=["meals"])
cdn = settings.s3.cdn_base_url


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
    locale: LocaleDependency,
) -> MealResponse:
    foods_result = await db.execute(
        select(MealFood, Food.image_key.label("food_image_key"))
        .join(Food, MealFood.food_id == Food.id)
        .where(MealFood.meal_id == meal.id, MealFood.user_id == meal.user_id)
    )
    drinks_result = await db.execute(
        select(MealDrink, Drink.image_key.label("drink_image_key"))
        .join(Drink, MealDrink.drink_id == Drink.id)
        .where(MealDrink.meal_id == meal.id, MealDrink.user_id == meal.user_id)
    )
    food_rows = foods_result.all()
    drink_rows = drinks_result.all()

    food_ids = [row.MealFood.food_id for row in food_rows]
    drink_ids = [row.MealDrink.drink_id for row in drink_rows]

    food_names = await batch_names(db, FoodTranslation, FoodTranslation.food_id, food_ids, locale)
    drink_names = await batch_names(db, DrinkTranslation, DrinkTranslation.drink_id, drink_ids, locale)

    foods = [
        {
            **{c.key: getattr(row.MealFood, c.key) for c in MealFood.__table__.columns},
            "food_name": food_names.get(row.MealFood.food_id, ""),
            "image_url": f"{cdn}/{row.food_image_key}" if row.food_image_key else None,
        }
        for row in food_rows
    ]
    drinks = [
        {
            **{c.key: getattr(row.MealDrink, c.key) for c in MealDrink.__table__.columns},
            "drink_name": drink_names.get(row.MealDrink.drink_id, ""),
            "image_url": f"{cdn}/{row.drink_image_key}" if row.drink_image_key else None,
        }
        for row in drink_rows
    ]
    return MealResponse.model_validate(
        {
            **{c.key: getattr(meal, c.key) for c in meal.__table__.columns},
            "foods": foods,
            "drinks": drinks,
        },
    )


@router.post("", response_model=MealResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(brand_limit("120/minute", "60/minute"), key_func=user_limit_strategy)
async def create_meal(
    request: Request,
    response: Response,
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


@router.post("/{meal_id}/foods", status_code=status.HTTP_201_CREATED)
@limiter.limit(brand_limit("120/minute", "60/minute"), key_func=user_limit_strategy)
async def add_meal_food(
    request: Request,
    response: Response,
    body: MealFoodCreate,
    db: DBSessionDependency,
    meal: MealDependency,
    locale: LocaleDependency,
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
    translations = await fetch_translations(db, FoodTranslation, FoodTranslation.food_id, [meal_food.food_id], locale)
    translation = translations.get(meal_food.food_id)
    image_url = f"{cdn}/{food.image_key}" if food.image_key else None
    food_name = translation.name if translation else ""
    return MealFoodResponse(**meal_food.model_dump(), food_name=food_name, image_url=image_url)


@router.patch("/{meal_id}/foods/{food_id}")
async def update_meal_food(
    body: MealFoodUpdate,
    db: DBSessionDependency,
    meal_food: MealFoodDependency,
    translation: MealFoodTranslationDependency,
) -> MealFoodResponse:
    meal_food.amount = body.amount
    await db.commit()
    await db.refresh(meal_food)
    food = await db.get(Food, meal_food.food_id)
    image_url = f"{cdn}/{food.image_key}" if food.image_key else None
    food_name = translation.name if translation else ""
    return MealFoodResponse(**meal_food.model_dump(), food_name=food_name, image_url=image_url)


@router.delete("/{meal_id}/foods/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_food(
    db: DBSessionDependency,
    meal_food: MealFoodDependency,
) -> None:
    await db.delete(meal_food)
    await db.commit()


@router.post("/{meal_id}/drinks", status_code=status.HTTP_201_CREATED)
@limiter.limit(brand_limit("120/minute", "60/minute"), key_func=user_limit_strategy)
async def add_meal_drink(
    request: Request,
    body: MealDrinkCreate,
    db: DBSessionDependency,
    meal: MealDependency,
    locale: LocaleDependency,
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
    translations = await fetch_translations(
        db, DrinkTranslation, DrinkTranslation.drink_id, [meal_drink.drink_id], locale
    )
    translation = translations.get(meal_drink.drink_id)
    image_url = f"{cdn}/{drink.image_key}" if drink.image_key else None
    return MealDrinkResponse(
        **meal_drink.model_dump(), drink_name=translation.name if translation else "", image_url=image_url
    )


@router.patch("/{meal_id}/drinks/{drink_id}")
async def update_meal_drink(
    body: MealDrinkUpdate,
    db: DBSessionDependency,
    meal_drink: MealDrinkDependency,
    translation: MealDrinkTranslationDependency,
) -> MealDrinkResponse:
    meal_drink.amount = body.amount
    await db.commit()
    await db.refresh(meal_drink)
    drink = await db.get(Drink, meal_drink.drink_id)
    image_url = f"{cdn}/{drink.image_key}" if drink.image_key else None
    return MealDrinkResponse(
        **meal_drink.model_dump(), drink_name=translation.name if translation else "", image_url=image_url
    )


@router.delete("/{meal_id}/drinks/{drink_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_drink(
    db: DBSessionDependency,
    meal_drink: MealDrinkDependency,
) -> None:
    await db.delete(meal_drink)
    await db.commit()
