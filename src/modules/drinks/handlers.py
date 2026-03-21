import asyncio
import builtins
import typing as t

from fastapi import APIRouter, Query
from sqlalchemy import select
from starlette import status

from libs.exceptions import TimeoutError
from libs.schemes import SearchResultList, SearchResultSchema
from libs.types import DBSessionDependency
from modules.drinks.dependencies import DrinkDependency
from modules.drinks.models import Drink
from modules.drinks.schemes import DrinkCreate, DrinkResponse, DrinkUpdate
from modules.drinks.tasks import generate_drink_embedding
from services.tasks import embed_text

router = APIRouter(prefix="/drinks", tags=["drinks"])


@router.get("", response_model=list[DrinkResponse])
async def list_drinks(
    db: DBSessionDependency,
    curated: t.Annotated[bool | None, Query()] = None,
    mine: t.Annotated[bool | None, Query()] = None,
) -> list[Drink]:
    stmt = select(Drink)
    if curated is True:
        stmt = stmt.where(Drink.curated.is_(True))
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/search", response_model=list[SearchResultSchema])
async def search_drinks(
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
            Drink.id,
            Drink.name,
            Drink.embedding.cosine_distance(query_embedding).label("score"),
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
) -> Drink:
    drink = Drink(**body.model_dump())
    db.add(drink)
    await db.commit()
    await db.refresh(drink)
    generate_drink_embedding.delay(drink.id)
    return drink


@router.patch("/{drink_id}", response_model=DrinkResponse)
async def update_drink(
    body: DrinkUpdate,
    db: DBSessionDependency,
    drink: DrinkDependency,
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
    drink: DrinkDependency,
) -> None:
    await db.delete(drink)
    await db.commit()
