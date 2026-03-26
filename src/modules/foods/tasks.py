from functools import partial

from core.celery import celery_app
from core.config import settings
from libs.s3 import get_s3_resource
from modules.foods.models import Food, FoodTranslation
from services.ingestible import generate_translation_embedding, process_entity_image

S3NoSuchKey = get_s3_resource().meta.client.exceptions.NoSuchKey

generate_embedding = partial(generate_translation_embedding, FoodTranslation, FoodTranslation.food_id)
process_image = partial(process_entity_image, Food)


@celery_app.task(max_retries=3, default_retry_delay=60)
def generate_food_embedding(food_id: str, locale: str = settings.default_locale) -> None:
    generate_embedding(food_id, locale)


@celery_app.task(
    acks_late=True,
    autoretry_for=(S3NoSuchKey,),
    max_retries=settings.s3.image_max_retries,
    default_retry_delay=settings.s3.image_retry_countdown,
)
def process_food_image(food_id: str, s3_key: str) -> None:
    process_image(food_id, s3_key)
