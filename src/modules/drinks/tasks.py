from core.celery import celery_app
from core.config import settings
from libs.s3 import get_s3_resource
from modules.drinks.models import Drink, DrinkTranslation
from services.ingestible import generate_translation_embedding, process_entity_image

S3NoSuchKey = get_s3_resource().meta.client.exceptions.NoSuchKey


@celery_app.task(max_retries=3, default_retry_delay=60)
def generate_drink_embedding(drink_id: str, locale: str = settings.default_locale) -> None:
    generate_translation_embedding(DrinkTranslation, DrinkTranslation.drink_id, drink_id, locale)


@celery_app.task(
    acks_late=True,
    autoretry_for=(S3NoSuchKey,),
    max_retries=settings.s3.image_max_retries,
    default_retry_delay=settings.s3.image_retry_countdown,
)
def process_drink_image(drink_id: str, s3_key: str) -> None:
    process_entity_image(Drink, drink_id, s3_key)
