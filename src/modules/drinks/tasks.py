import logging

from sqlalchemy import update
from sqlalchemy.orm import Session

from core.celery import celery_app
from core.database import get_sync_engine
from modules.drinks.models import Drink
from services.tasks import embed_text

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_drink_embedding(self, drink_id: str) -> None:
    with Session(get_sync_engine()) as session:
        drink = session.get(Drink, drink_id)
        if drink is None:
            logger.warning("Drink %s not found, skipping embedding", drink_id)
            return

        embedding = embed_text(drink.name)
        session.execute(update(Drink).where(Drink.id == drink_id).values(embedding=embedding))
        session.commit()
