import asyncio
import builtins
import typing as t

from fastapi import APIRouter, Query
from sqlalchemy import func, select
from starlette import status

from libs.exceptions import TimeoutError
from libs.schemes import SearchResultList, SearchResultSchema
from libs.types import DBSessionDependency
from modules.foods.dependencies import FoodDependency
from modules.foods.models import Food
from modules.foods.schemes import FoodCreate, FoodResponse, FoodUpdate
from modules.foods.tasks import generate_food_embedding
from services.tasks import embed_text

router = APIRouter(prefix="/foods", tags=["foods"])


@router.get("", response_model=list[FoodResponse])
async def list_foods(
    db: DBSessionDependency,
    curated: t.Annotated[bool | None, Query()] = None,
    mine: t.Annotated[bool | None, Query()] = None,
) -> list[Food]:
    stmt = select(Food)
    if curated is True:
        stmt = stmt.where(Food.curated.is_(True))
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/search", response_model=list[SearchResultSchema])
async def search_foods(
    db: DBSessionDependency,
    q: t.Annotated[str, Query(min_length=1)],
    limit: t.Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[SearchResultSchema]:
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
            Food.id,
            Food.name,
            func.round(Food.embedding.cosine_distance(query_embedding), 3).label("score"),
        )
        .where(Food.embedding.is_not(None))
        .order_by("score")
        .limit(limit)
    )
    result = await db.execute(stmt)
    return SearchResultList.validate_python(result.mappings().all())


@router.get("/{food_id}", response_model=FoodResponse)
async def get_food(
    food: FoodDependency,
) -> Food:
    return food


@router.post("", response_model=FoodResponse, status_code=status.HTTP_201_CREATED)
async def create_food(
    body: FoodCreate,
    db: DBSessionDependency,
) -> Food:
    food = Food(**body.model_dump())
    db.add(food)
    await db.commit()
    await db.refresh(food)
    generate_food_embedding.delay(food.id)
    return food


@router.patch("/{food_id}", response_model=FoodResponse)
async def update_food(
    body: FoodUpdate,
    db: DBSessionDependency,
    food: FoodDependency,
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
    food: FoodDependency,
) -> None:
    await db.delete(food)
    await db.commit()
