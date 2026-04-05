import asyncio
import builtins
import typing as t

from fastapi import APIRouter, Query, Request, Response
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
from services.ratelimit import brand_limit, ip_limit_strategy, limiter, user_limit_strategy
from services.tasks import embed_text
from utils.fastapi import (
    RESPONSES_AUTH,
    RESPONSES_CONFLICT,
    RESPONSES_FORBIDDEN,
    RESPONSES_NOT_FOUND,
    RESPONSES_RATE_LIMIT,
    RESPONSES_TIMEOUT,
    merge_responses,
)

router = APIRouter(prefix="/foods", tags=["foods"])


@router.get("", summary="List foods")
async def list_foods(
    db: DBSessionDependency,
    user: OptionalUserDependency,
    pagination: PaginationDependency,
    locale: LocaleDependency,
    mine: t.Annotated[bool | None, Query(description="If true, return only items created by the current user")] = None,
) -> CursorPage[FoodResponse]:
    stmt = select(Food).where(ingestible_visible_filter(Food, user))
    if mine is True and user is not None:
        stmt = stmt.where(Food.creator_id == user.id)
    page = await paginate(db, stmt, Food, pagination)

    food_ids = [f.id for f in page.items]
    translations = await fetch_translations(db, FoodTranslation, FoodTranslation.food_id, food_ids, locale)
    items = [apply_translation(f, translations.get(f.id), FoodResponse) for f in page.items]
    return CursorPage(items=items, total=page.total, next_cursor=page.next_cursor)


@router.get(
    "/search", summary="Semantic search for foods", responses=merge_responses(RESPONSES_TIMEOUT, RESPONSES_RATE_LIMIT)
)
@limiter.limit(brand_limit("60/minute", "30/minute"), key_func=user_limit_strategy)
@limiter.limit(brand_limit("20/minute", "5/minute"), key_func=ip_limit_strategy)
async def search_foods(
    request: Request,
    response: Response,
    db: DBSessionDependency,
    _user: OptionalUserDependency,
    locale: LocaleDependency,
    q: t.Annotated[str, Query(min_length=1, description="Natural-language search query")],
    limit: t.Annotated[int, Query(ge=1, le=100, description="Maximum search results")] = 20,
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


@router.get("/{pk}", summary="Get a food by ID", responses=RESPONSES_NOT_FOUND)
async def get_food(
    food: FoodDependency,
    translation: FoodTranslationDependency,
) -> FoodResponse:
    return apply_translation(food, translation, FoodResponse)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a food",
    responses=merge_responses(RESPONSES_AUTH, RESPONSES_RATE_LIMIT),
)
@limiter.limit(brand_limit("60/minute", "30/minute"), key_func=user_limit_strategy)
@limiter.limit(brand_limit("20/minute", "5/minute"), key_func=ip_limit_strategy)
async def create_food(
    request: Request,
    response: Response,
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


@router.patch(
    "/{pk}",
    summary="Update a food",
    responses=merge_responses(RESPONSES_AUTH, RESPONSES_NOT_FOUND, RESPONSES_FORBIDDEN),
)
@limiter.limit(brand_limit("120/minute", "60/minute"), key_func=user_limit_strategy)
async def update_food(
    request: Request,
    response: Response,
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


@router.delete(
    "/{pk}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a food",
    responses=merge_responses(RESPONSES_AUTH, RESPONSES_NOT_FOUND, RESPONSES_FORBIDDEN),
)
@limiter.limit(brand_limit("120/minute", "60/minute"), key_func=user_limit_strategy)
async def delete_food(
    request: Request,
    response: Response,
    db: DBSessionDependency,
    food: WritableFoodDependency,
) -> None:
    await db.delete(food)
    await db.commit()


@router.post(
    "/{pk}/image",
    summary="Get a presigned URL for food image upload",
    responses=merge_responses(RESPONSES_AUTH, RESPONSES_NOT_FOUND, RESPONSES_CONFLICT),
)
@limiter.limit(brand_limit("10/minute", "5/minute"), key_func=user_limit_strategy)
@limiter.limit(brand_limit("5/minute", "2/minute"), key_func=ip_limit_strategy)
async def upload_food_image(
    request: Request,
    response: Response,
    food: WritableFoodDependency,
    db: DBSessionDependency,
    image_manager: ImageManagerDependency,
    content_type: t.Annotated[ImageContentType, Query(description="MIME type of the image to upload")],
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
