import asyncio
import builtins
import typing as t

from fastapi import APIRouter, Query
from sqlalchemy import func, select
from starlette import status

from libs.db import ingestible_visible_filter
from libs.exceptions import TimeoutError
from libs.schemes import SearchResultList, SearchResultSchema
from libs.types import DBSessionDependency
from modules.drinks.dependencies import DrinkDependency, WritableDrinkDependency
from modules.drinks.models import Drink
from modules.drinks.schemes import DrinkCreate, DrinkResponse, DrinkUpdate
from modules.drinks.tasks import generate_drink_embedding
from modules.users.dependencies import CurrentUserDependency, OptionalUserDependency
from services.tasks import embed_text

router = APIRouter(prefix="/drinks", tags=["drinks"])


@router.get("", response_model=list[DrinkResponse])
async def list_drinks(
    db: DBSessionDependency,
    user: OptionalUserDependency,
    mine: t.Annotated[bool | None, Query()] = None,
) -> list[Drink]:
    stmt = select(Drink).where(ingestible_visible_filter(Drink, user))
    if mine is True and user is not None:
        stmt = stmt.where(Drink.creator_id == user.id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/search", response_model=list[SearchResultSchema])
async def search_drinks(
    db: DBSessionDependency,
    _user: OptionalUserDependency,
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
            Drink.id,
            Drink.name,
            func.round(Drink.embedding.cosine_distance(query_embedding), 3).label("score"),
        )
        .where(Drink.embedding.is_not(None))
        .order_by("score")
        .limit(limit)
    )
    result = await db.execute(stmt)
    return SearchResultList.validate_python(result.mappings().all())


@router.get("/{drink_id}", response_model=DrinkResponse)
async def get_drink(
    drink: DrinkDependency,
) -> Drink:
    return drink


@router.post("", response_model=DrinkResponse, status_code=status.HTTP_201_CREATED)
async def create_drink(
    body: DrinkCreate,
    db: DBSessionDependency,
    user: CurrentUserDependency,
) -> Drink:
    drink = Drink(**body.model_dump(), creator_id=user.id)
    db.add(drink)
    await db.commit()
    await db.refresh(drink)
    generate_drink_embedding.delay(drink.id)
    return drink


@router.patch("/{drink_id}", response_model=DrinkResponse)
async def update_drink(
    body: DrinkUpdate,
    db: DBSessionDependency,
    drink: WritableDrinkDependency,
) -> Drink:
    updates = body.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(drink, key, value)
    await db.commit()
    await db.refresh(drink)
    if "name" in updates:
        generate_drink_embedding.delay(drink.id)
    return drink


@router.delete("/{drink_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_drink(
    db: DBSessionDependency,
    drink: WritableDrinkDependency,
) -> None:
    await db.delete(drink)
    await db.commit()
