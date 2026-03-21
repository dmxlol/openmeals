import logging

from sqlalchemy import update
from sqlalchemy.orm import Session

from core.celery import celery_app
from core.database import get_sync_engine
from modules.foods.models import Food
from services.tasks import embed_text

logger = logging.getLogger(__name__)


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
