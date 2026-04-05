import typing as t

from pydantic import PrivateAttr, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from libs.embeddings.config import MockConfig, OpenAIConfig, SentenceTransformerConfig, TritonConfig

from . import ENVIRONMENT


class CelerySettings(BaseSettings):
    broker_url: str
    result_backend: str

    model_config = SettingsConfigDict(env_prefix="CELERY_")


class OtelSettings(BaseSettings):
    enabled: bool = False
    service_name: str = "openmeals"

    model_config = SettingsConfigDict(env_prefix="OTEL_")


class S3Settings(BaseSettings):
    bucket: str = ""
    cdn_base_url: str = ""
    presigned_url_expiry_seconds: int = 300
    image_max_dimension: int = 1200
    image_webp_quality: int = 85
    image_cache_max_age: int = 31536000
    image_max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB
    image_upload_countdown: int = 10
    image_retry_countdown: int = 15
    image_max_retries: int = 20

    model_config = SettingsConfigDict(env_prefix="S3_")


class EmbeddingSettings(BaseSettings):
    provider: t.Literal["sentence-transformers", "triton", "openai", "mock"] = "sentence-transformers"

    _config: SentenceTransformerConfig | TritonConfig | OpenAIConfig | MockConfig = PrivateAttr()

    model_config = SettingsConfigDict(env_prefix="EMBEDDING_")

    def model_post_init(self, __context: t.Any) -> None:
        match self.provider:
            case "sentence-transformers":
                self._config = SentenceTransformerConfig()
            case "triton":
                self._config = TritonConfig()
            case "openai":
                self._config = OpenAIConfig()
            case "mock":
                self._config = MockConfig()

    @property
    def config(self) -> SentenceTransformerConfig | TritonConfig | OpenAIConfig | MockConfig:
        return self._config


class Settings(BaseSettings):
    def __hash__(self) -> int:
        return id(self)

    env: str = ENVIRONMENT
    version: str = "0.0.1a"

    redis_url: str = "redis://localhost:6379/0"

    clients: dict[str, str] = {}  # brand → PEM public key, e.g. CLIENTS__OPENPEEL=<pubkey>
    allowed_ips: list[str] = []

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
    default_locale: str = "en-US"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    celery: CelerySettings = CelerySettings()

    s3: S3Settings = S3Settings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    otel: OtelSettings = OtelSettings()

    model_config = SettingsConfigDict(extra="ignore")


settings = Settings()
