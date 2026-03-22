import logging

from sqlalchemy import update
from sqlalchemy.orm import Session

from core.celery import celery_app
from core.config import settings
from core.database import get_sync_engine
from libs.s3 import get_s3_resource
from modules.foods.models import Food
from services.tasks import embed_text, process_image_file

logger = logging.getLogger(__name__)

S3NoSuchKey = get_s3_resource().meta.client.exceptions.NoSuchKey


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_food_embedding(self, food_id: str) -> None:
    with Session(get_sync_engine()) as session:
        food = session.get(Food, food_id)
        if food is None:
            logger.warning("Food %s not found, skipping embedding", food_id)
            return

        embedding = embed_text(food.name)
        session.execute(update(Food).where(Food.id == food_id).values(embedding=embedding))
        session.commit()


@celery_app.task(
    bind=True,
    acks_late=True,
    autoretry_for=(S3NoSuchKey,),
    max_retries=settings.s3.image_max_retries,
    default_retry_delay=settings.s3.image_retry_countdown,
)
def process_food_image(self, food_id: str, s3_key: str) -> None:
    bucket = get_s3_resource().Bucket(settings.s3.bucket)
    processed_key = process_image_file(
        bucket=bucket,
        raw_key=s3_key,
        entity_type=Food.__tablename__,
        entity_id=food_id,
    )

    with Session(get_sync_engine()) as session:
        session.execute(update(Food).where(Food.id == food_id).values(image_key=processed_key))
        session.commit()

    logger.info("Processed image for food/%s -> %s", food_id, processed_key)
