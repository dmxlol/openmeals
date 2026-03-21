import typing as t
from functools import lru_cache

from libs.embeddings.base import EmbeddingProvider
from libs.embeddings.factory import create_embedding_provider

if t.TYPE_CHECKING:
    from core.config import Settings


@lru_cache(maxsize=1)
def get_embedding_provider(settings: "Settings") -> EmbeddingProvider:
    return create_embedding_provider(settings)


__all__ = ["EmbeddingProvider", "create_embedding_provider", "get_embedding_provider"]
