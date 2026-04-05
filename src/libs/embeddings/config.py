from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class SentenceTransformerConfig(BaseSettings):
    model: str = "intfloat/multilingual-e5-base"
    dimension: int = 768

    model_config = SettingsConfigDict(env_prefix="EMBEDDING_")


class TritonConfig(BaseSettings):
    url: str
    model: str = "intfloat/multilingual-e5-base"
    dimension: int = 768

    model_config = SettingsConfigDict(env_prefix="EMBEDDING_")


class OpenAIConfig(BaseSettings):
    api_key: SecretStr
    model: str = "text-embedding-3-small"
    dimension: int = 1536

    model_config = SettingsConfigDict(env_prefix="EMBEDDING_")


class MockConfig(BaseSettings):
    dimension: int = 768

    model_config = SettingsConfigDict(env_prefix="EMBEDDING_")
