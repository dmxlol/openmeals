import logging

from sqlalchemy import update
from sqlalchemy.orm import InstrumentedAttribute, Session
from sqlmodel import SQLModel

from core.config import settings
from core.database import get_sync_engine
from libs.s3 import get_s3_resource
from services.tasks import embed_text, process_image_file

logger = logging.getLogger(__name__)


def generate_translation_embedding(
    translation_model: type[SQLModel],
    id_col: InstrumentedAttribute,
    entity_id: str,
    locale: str,
) -> None:
    with Session(get_sync_engine()) as session:
        translation = session.get(translation_model, (entity_id, locale))
        if translation is None:
            logger.warning("No %s translation for %s, skipping embedding", locale, entity_id)
            return
        embedding = embed_text(translation.name)
        session.execute(
            update(translation_model)
            .where(id_col == entity_id, translation_model.locale == locale)
            .values(embedding=embedding)
        )
        session.commit()


def process_entity_image(main_model: type[SQLModel], entity_id: str, s3_key: str) -> None:
    bucket = get_s3_resource().Bucket(settings.s3.bucket)
    processed_key = process_image_file(
        bucket=bucket,
        raw_key=s3_key,
        entity_type=main_model.__tablename__,
        entity_id=entity_id,
    )
    with Session(get_sync_engine()) as session:
        session.execute(update(main_model).where(main_model.id == entity_id).values(image_key=processed_key))
        session.commit()
    logger.info("Processed image for %s/%s -> %s", main_model.__tablename__, entity_id, processed_key)
