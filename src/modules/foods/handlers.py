import asyncio
import builtins
import typing as t

from fastapi import APIRouter, Query
from sqlalchemy import Numeric, cast, func, select
from starlette import status

from core.config import settings
from core.schemes import CursorPage
from libs.db import ingestible_visible_filter
from libs.exceptions import ConflictError, TimeoutError
from libs.pagination import PaginationDependency, paginate
from libs.schemes import ImageUploadResponse
from libs.translations import apply_translation, fetch_translations
from libs.types import DBSessionDependency
from modules.foods.dependencies import FoodDependency, FoodTranslationDependency, WritableFoodDependency
from modules.foods.models import Food, FoodTranslation
from modules.foods.schemes import (
    FoodCreate,
    FoodResponse,
    FoodSearchResult,
    FoodUpdate,
)
from modules.foods.tasks import generate_food_embedding, process_food_image
from modules.users.dependencies import CurrentUserDependency, LocaleDependency, OptionalUserDependency
from services.image import ImageContentType, ImageManagerDependency
from services.tasks import embed_text

router = APIRouter(prefix="/foods", tags=["foods"])


@router.get("")
async def list_foods(
    db: DBSessionDependency,
    user: OptionalUserDependency,
    pagination: PaginationDependency,
    locale: LocaleDependency,
    mine: t.Annotated[bool | None, Query()] = None,
) -> CursorPage[FoodResponse]:
    stmt = select(Food).where(ingestible_visible_filter(Food, user))
    if mine is True and user is not None:
        stmt = stmt.where(Food.creator_id == user.id)
    page = await paginate(db, stmt, Food, pagination)

    food_ids = [f.id for f in page.items]
    translations = await fetch_translations(db, FoodTranslation, FoodTranslation.food_id, food_ids, locale)
    items = [apply_translation(f, translations.get(f.id), FoodResponse) for f in page.items]
    return CursorPage(items=items, total=page.total, next_cursor=page.next_cursor)


@router.get("/search")
async def search_foods(
    db: DBSessionDependency,
    _user: OptionalUserDependency,
    locale: LocaleDependency,
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
            func.round(cast(FoodTranslation.embedding.cosine_distance(query_embedding), Numeric), 3).label("score"),
        )
        .join(
            FoodTranslation,
            (FoodTranslation.food_id == Food.id) & (FoodTranslation.locale == settings.default_locale),
        )
        .where(FoodTranslation.embedding.is_not(None))
        .order_by("score")
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()

    food_ids = [row.Food.id for row in rows]
    translations = await fetch_translations(db, FoodTranslation, FoodTranslation.food_id, food_ids, locale)
    return [
        FoodSearchResult(
            **apply_translation(row.Food, translations.get(row.Food.id), FoodResponse).model_dump(),
            score=row.score,
        )
        for row in rows
    ]


@router.get("/{pk}")
async def get_food(
    food: FoodDependency,
    translation: FoodTranslationDependency,
) -> FoodResponse:
    return apply_translation(food, translation, FoodResponse)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_food(
    body: FoodCreate,
    db: DBSessionDependency,
    user: CurrentUserDependency,
) -> FoodResponse:
    data = body.model_dump()
    name = data.pop("name")
    food = Food(**data, creator_id=user.id)
    db.add(food)
    await db.flush()
    translation = FoodTranslation(food_id=food.id, locale=settings.default_locale, name=name)
    db.add(translation)
    await db.commit()
    await db.refresh(food)
    await db.refresh(translation)
    generate_food_embedding.delay(food.id)
    return apply_translation(food, translation, FoodResponse)


@router.patch("/{pk}")
async def update_food(
    body: FoodUpdate,
    db: DBSessionDependency,
    food: WritableFoodDependency,
) -> FoodResponse:
    updates = body.model_dump(exclude_unset=True)
    name = updates.pop("name", None)
    for key, value in updates.items():
        setattr(food, key, value)

    en_us_tr = await db.get(FoodTranslation, (food.id, settings.default_locale))
    if name is not None:
        if en_us_tr is None:
            en_us_tr = FoodTranslation(food_id=food.id, locale=settings.default_locale, name=name)
            db.add(en_us_tr)
        else:
            en_us_tr.name = name
        generate_food_embedding.delay(food.id)

    await db.commit()
    await db.refresh(food)
    if en_us_tr is not None:
        await db.refresh(en_us_tr)

    return apply_translation(food, en_us_tr, FoodResponse)


@router.delete("/{pk}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_food(
    db: DBSessionDependency,
    food: WritableFoodDependency,
) -> None:
    await db.delete(food)
    await db.commit()


@router.post("/{pk}/image")
async def upload_food_image(
    food: WritableFoodDependency,
    db: DBSessionDependency,
    image_manager: ImageManagerDependency,
    content_type: t.Annotated[ImageContentType, Query()],
) -> ImageUploadResponse:
    if food.image_key and food.image_key.startswith("raw/"):
        raise ConflictError("Image upload already in progress")
    result = image_manager.generate_upload_url(
        entity_type=Food.__tablename__,
        entity_id=str(food.id),
        content_type=content_type,
    )
    food.image_key = result.raw_key
    await db.commit()
    process_food_image.apply_async(
        args=(str(food.id), result.raw_key),
        countdown=settings.s3.image_upload_countdown,
    )
    return ImageUploadResponse(upload_url=result.upload_url, upload_fields=result.upload_fields)
