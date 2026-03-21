# ruff: noqa: PLC0415
import typing as t

if t.TYPE_CHECKING:
    from core.config import Settings

    from .base import EmbeddingProvider


def create_embedding_provider(settings: "Settings") -> "EmbeddingProvider":
    match settings.embedding.provider:
        case "sentence-transformers":
            from libs.embeddings.sentence_transformer import SentenceTransformerProvider

            return SentenceTransformerProvider(model_name=settings.embedding.model)
        case "triton":
            from libs.embeddings.triton import TritonProvider

            return TritonProvider(
                url=settings.embedding.triton_url,
                model_name=settings.embedding.model,
                dimension=settings.embedding.dimension,
            )
        case "openai":
            from libs.embeddings.openai import OpenAIProvider

            return OpenAIProvider(
                api_key=settings.embedding.openai_api_key.get_secret_value(),
                model_name=settings.embedding.model,
                dimension=settings.embedding.dimension,
            )
        case _:
            msg = f"Unknown embedding provider: {settings.embedding.provider}"
            raise ValueError(msg)
