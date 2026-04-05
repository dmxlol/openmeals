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
from modules.drinks.dependencies import DrinkDependency, DrinkTranslationDependency, WritableDrinkDependency
from modules.drinks.models import Drink, DrinkTranslation
from modules.drinks.schemes import (
    DrinkCreate,
    DrinkResponse,
    DrinkSearchResult,
    DrinkUpdate,
)
from modules.drinks.tasks import generate_drink_embedding, process_drink_image
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

router = APIRouter(prefix="/drinks", tags=["drinks"])


@router.get("", summary="List drinks")
async def list_drinks(
    db: DBSessionDependency,
    user: OptionalUserDependency,
    pagination: PaginationDependency,
    locale: LocaleDependency,
    mine: t.Annotated[bool | None, Query(description="If true, return only items created by the current user")] = None,
) -> CursorPage[DrinkResponse]:
    stmt = select(Drink).where(ingestible_visible_filter(Drink, user))
    if mine is True and user is not None:
        stmt = stmt.where(Drink.creator_id == user.id)
    page = await paginate(db, stmt, Drink, pagination)

    drink_ids = [d.id for d in page.items]
    translations = await fetch_translations(db, DrinkTranslation, DrinkTranslation.drink_id, drink_ids, locale)
    items = [apply_translation(d, translations.get(d.id), DrinkResponse) for d in page.items]
    return CursorPage(items=items, total=page.total, next_cursor=page.next_cursor)


@router.get(
    "/search", summary="Semantic search for drinks", responses=merge_responses(RESPONSES_TIMEOUT, RESPONSES_RATE_LIMIT)
)
@limiter.limit(brand_limit("60/minute", "30/minute"), key_func=user_limit_strategy)
@limiter.limit(brand_limit("20/minute", "5/minute"), key_func=ip_limit_strategy)
async def search_drinks(
    request: Request,
    response: Response,
    db: DBSessionDependency,
    _user: OptionalUserDependency,
    locale: LocaleDependency,
    q: t.Annotated[str, Query(min_length=1, description="Natural-language search query")],
    limit: t.Annotated[int, Query(ge=1, le=100, description="Maximum search results")] = 20,
) -> list[DrinkSearchResult]:
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
            Drink,
            func.round(cast(DrinkTranslation.embedding.cosine_distance(query_embedding), Numeric), 3).label("score"),
        )
        .join(
            DrinkTranslation,
            (DrinkTranslation.drink_id == Drink.id) & (DrinkTranslation.locale == settings.default_locale),
        )
        .where(DrinkTranslation.embedding.is_not(None))
        .order_by("score")
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()

    drink_ids = [row.Drink.id for row in rows]
    translations = await fetch_translations(db, DrinkTranslation, DrinkTranslation.drink_id, drink_ids, locale)
    return [
        DrinkSearchResult(
            **apply_translation(row.Drink, translations.get(row.Drink.id), DrinkResponse).model_dump(),
            score=row.score,
        )
        for row in rows
    ]


@router.get("/{pk}", summary="Get a drink by ID", responses=RESPONSES_NOT_FOUND)
async def get_drink(
    drink: DrinkDependency,
    translation: DrinkTranslationDependency,
) -> DrinkResponse:
    return apply_translation(drink, translation, DrinkResponse)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a drink",
    responses=merge_responses(RESPONSES_AUTH, RESPONSES_RATE_LIMIT),
)
@limiter.limit(brand_limit("60/minute", "30/minute"), key_func=user_limit_strategy)
@limiter.limit(brand_limit("20/minute", "5/minute"), key_func=ip_limit_strategy)
async def create_drink(
    request: Request,
    response: Response,
    body: DrinkCreate,
    db: DBSessionDependency,
    user: CurrentUserDependency,
) -> DrinkResponse:
    data = body.model_dump()
    name = data.pop("name")
    drink = Drink(**data, creator_id=user.id)
    db.add(drink)
    await db.flush()
    translation = DrinkTranslation(drink_id=drink.id, locale=settings.default_locale, name=name)
    db.add(translation)
    await db.commit()
    await db.refresh(drink)
    await db.refresh(translation)
    generate_drink_embedding.delay(drink.id)
    return apply_translation(drink, translation, DrinkResponse)


@router.patch(
    "/{pk}",
    summary="Update a drink",
    responses=merge_responses(RESPONSES_AUTH, RESPONSES_NOT_FOUND, RESPONSES_FORBIDDEN),
)
@limiter.limit(brand_limit("120/minute", "60/minute"), key_func=user_limit_strategy)
async def update_drink(
    request: Request,
    response: Response,
    body: DrinkUpdate,
    db: DBSessionDependency,
    drink: WritableDrinkDependency,
) -> DrinkResponse:
    updates = body.model_dump(exclude_unset=True)
    name = updates.pop("name", None)
    for key, value in updates.items():
        setattr(drink, key, value)

    en_us_tr = await db.get(DrinkTranslation, (drink.id, settings.default_locale))
    if name is not None:
        if en_us_tr is None:
            en_us_tr = DrinkTranslation(drink_id=drink.id, locale=settings.default_locale, name=name)
            db.add(en_us_tr)
        else:
            en_us_tr.name = name
        generate_drink_embedding.delay(drink.id)

    await db.commit()
    await db.refresh(drink)
    if en_us_tr is not None:
        await db.refresh(en_us_tr)

    return apply_translation(drink, en_us_tr, DrinkResponse)


@router.delete(
    "/{pk}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a drink",
    responses=merge_responses(RESPONSES_AUTH, RESPONSES_NOT_FOUND, RESPONSES_FORBIDDEN),
)
@limiter.limit(brand_limit("120/minute", "60/minute"), key_func=user_limit_strategy)
async def delete_drink(
    request: Request,
    response: Response,
    db: DBSessionDependency,
    drink: WritableDrinkDependency,
) -> None:
    await db.delete(drink)
    await db.commit()


@router.post(
    "/{pk}/image",
    summary="Get a presigned URL for drink image upload",
    responses=merge_responses(RESPONSES_AUTH, RESPONSES_NOT_FOUND, RESPONSES_CONFLICT),
)
@limiter.limit(brand_limit("10/minute", "5/minute"), key_func=user_limit_strategy)
@limiter.limit(brand_limit("5/minute", "2/minute"), key_func=ip_limit_strategy)
async def upload_drink_image(
    request: Request,
    response: Response,
    drink: WritableDrinkDependency,
    db: DBSessionDependency,
    image_manager: ImageManagerDependency,
    content_type: t.Annotated[ImageContentType, Query(description="MIME type of the image to upload")],
) -> ImageUploadResponse:
    if drink.image_key and drink.image_key.startswith("raw/"):
        raise ConflictError("Image upload already in progress")
    result = image_manager.generate_upload_url(
        entity_type=Drink.__tablename__,
        entity_id=str(drink.id),
        content_type=content_type,
    )
    drink.image_key = result.raw_key
    await db.commit()
    process_drink_image.apply_async(
        args=(str(drink.id), result.raw_key),
        countdown=settings.s3.image_upload_countdown,
    )
    return ImageUploadResponse(upload_url=result.upload_url, upload_fields=result.upload_fields)
