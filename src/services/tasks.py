from core.celery import celery_app
from core.config import settings
from libs.embeddings import get_embedding_provider


@celery_app.task
def embed_text(text: str) -> list[float]:
    provider = get_embedding_provider(settings)
    [embedding] = provider.embed([text])
    return embedding
