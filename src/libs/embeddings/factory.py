# ruff: noqa: PLC0415
import typing as t

from libs.embeddings.config import MockConfig, OpenAIConfig, SentenceTransformerConfig, TritonConfig

if t.TYPE_CHECKING:
    from core.config import Settings

    from .base import EmbeddingProvider


def create_embedding_provider(settings: "Settings") -> "EmbeddingProvider":
    match settings.embedding.config:
        case SentenceTransformerConfig() as cfg:
            from libs.embeddings.sentence_transformer import SentenceTransformerProvider

            return SentenceTransformerProvider(model_name=cfg.model)
        case TritonConfig() as cfg:
            from libs.embeddings.triton import TritonProvider

            return TritonProvider(url=cfg.url, model_name=cfg.model, dimension=cfg.dimension)
        case OpenAIConfig() as cfg:
            from libs.embeddings.openai import OpenAIProvider

            return OpenAIProvider(
                api_key=cfg.api_key.get_secret_value(),
                model_name=cfg.model,
                dimension=cfg.dimension,
            )
        case MockConfig() as cfg:
            from libs.embeddings.mock import MockProvider

            return MockProvider(dimension=cfg.dimension)
