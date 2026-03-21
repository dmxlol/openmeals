import typing as t

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from . import ENVIRONMENT


class CelerySettings(BaseSettings):
    broker_url: str
    result_backend: str

    model_config = SettingsConfigDict(env_prefix="CELERY_")


class EmbeddingSettings(BaseSettings):
    provider: t.Literal["sentence-transformers", "triton", "openai"] = "sentence-transformers"
    model: str = "intfloat/multilingual-e5-base"
    dimension: int = 768
    model_config = SettingsConfigDict(env_prefix="EMBEDDING_")


class Settings(BaseSettings):
    def __hash__(self) -> int:
        return id(self)

    env: str = ENVIRONMENT
    version: str = "0.0.1a"

    modules: t.ClassVar[list] = [
        "modules.auth",
        "modules.drinks",
        "modules.foods",
        "modules.meals",
        "modules.summaries",
        "modules.users",
    ]

    database_url: SecretStr
    secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    google_client_id: str
    google_client_secret: SecretStr

    celery: CelerySettings = CelerySettings()
    aws_region: str = "eu-central-1"

    anthropic_api_key: SecretStr
    anthropic_model: str = "claude-sonnet-4-6"

    embedding: "EmbeddingSettings" = EmbeddingSettings()

    model_config = SettingsConfigDict(extra="ignore")


settings = Settings()
