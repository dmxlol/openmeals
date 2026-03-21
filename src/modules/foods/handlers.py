import asyncio
import builtins
import typing as t

from fastapi import APIRouter, Query
from sqlalchemy import func, select
from starlette import status

from core.schemes import CursorPage
from libs.db import ingestible_visible_filter
from libs.exceptions import TimeoutError
from libs.pagination import PaginationDependency, paginate
from libs.types import DBSessionDependency
from modules.foods.dependencies import FoodDependency, WritableFoodDependency
from modules.foods.models import Food
from modules.foods.schemes import FoodCreate, FoodResponse, FoodSearchResult, FoodUpdate
from modules.foods.tasks import generate_food_embedding
from modules.users.dependencies import CurrentUserDependency, OptionalUserDependency
from services.tasks import embed_text

router = APIRouter(prefix="/foods", tags=["foods"])


@router.get("", response_model=CursorPage[FoodResponse])
async def list_foods(
    db: DBSessionDependency,
    user: OptionalUserDependency,
    pagination: PaginationDependency,
    mine: t.Annotated[bool | None, Query()] = None,
) -> CursorPage[Food]:
    stmt = select(Food).where(ingestible_visible_filter(Food, user))
    if mine is True and user is not None:
        stmt = stmt.where(Food.creator_id == user.id)
    return await paginate(db, stmt, Food, pagination)


@router.get("/search")
async def search_foods(
    db: DBSessionDependency,
    _user: OptionalUserDependency,
    q: t.Annotated[str, Query(min_length=1)],
    limit: t.Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[FoodSearchResult]:
    try:
        task_result = embed_text.delay(q)
        query_embedding = await asyncio.wait_for(
            asyncio.to_thread(task_result.get, timeout=100),
            timeout=110,
        )
    except builtins.TimeoutError as e:
        raise TimeoutError("Embedding generation timed out") from e

    stmt = (
        select(
            Food,
            func.round(Food.embedding.cosine_distance(query_embedding), 3).label("score"),
        )
        .where(Food.embedding.is_not(None))
        .order_by("score")
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [FoodSearchResult.model_validate(row.Food, update={"score": row.score}) for row in result.all()]


@router.get("/{food_id}", response_model=FoodResponse)
async def get_food(
    food: FoodDependency,
) -> Food:
    return food


@router.post("", response_model=FoodResponse, status_code=status.HTTP_201_CREATED)
async def create_food(
    body: FoodCreate,
    db: DBSessionDependency,
    user: CurrentUserDependency,
) -> Food:
    food = Food(**body.model_dump(), creator_id=user.id)
    db.add(food)
    await db.commit()
    await db.refresh(food)
    generate_food_embedding.delay(food.id)
    return food


@router.patch("/{food_id}", response_model=FoodResponse)
async def update_food(
    body: FoodUpdate,
    db: DBSessionDependency,
    food: WritableFoodDependency,
) -> Food:
    updates = body.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(food, key, value)
    await db.commit()
    await db.refresh(food)
    if "name" in updates:
        generate_food_embedding.delay(food.id)
    return food


@router.delete("/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_food(
    db: DBSessionDependency,
    food: WritableFoodDependency,
) -> None:
    await db.delete(food)
    await db.commit()
