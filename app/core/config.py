"""Application configuration (Pydantic Settings v2).

Use ``APP_ENV`` (alias ``ENVIRONMENT``) to select lifecycle: ``local``, ``development``,
``staging``, ``production``.
"""

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    APP_ENV: Literal["local", "development", "staging", "production"] = Field(
        default="local",
        validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"),
    )

    DATABASE_URL: str = Field(
        ...,
        description="Async SQLAlchemy URL, e.g. postgresql+asyncpg://user:pass@host:5432/db",
    )

    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    CORS_ORIGINS: str = Field(
        default="http://localhost:3000",
        description="Comma-separated origins for CORS",
    )

    RATE_LIMIT_ENABLED: bool = False

    JWT_SECRET_KEY: str = Field(
        default="dev-insecure-comet-secret-change-in-production",
        description="HS256 secret for access tokens (set in staging/prod)",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    CELERY_BROKER_URL: str | None = Field(
        default=None,
        description="Defaults to REDIS_URL when unset",
    )

    MATCHING_OFFER_TTL_SECONDS: int = 60
    DRIVER_LOCATION_DB_THROTTLE_SECONDS: int = 30

    NEW_RELIC_LICENSE_KEY: str | None = None
    NEW_RELIC_APP_NAME: str = "comet-api"
    NEW_RELIC_LOG: str = "stdout"
    NEW_RELIC_DISTRIBUTED_TRACING_ENABLED: bool = True

    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origin_list(self) -> list[str]:
        raw = self.CORS_ORIGINS.strip()
        if not raw:
            return []
        return [part.strip() for part in raw.split(",") if part.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def exposes_internal_errors(self) -> bool:
        """Non-sensitive error detail for unexpected exceptions (staging/prod hides by default)."""

        return self.APP_ENV in ("local", "development")

    @property
    def celery_broker_url(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def rate_limit_storage_uri(self) -> str:
        if self.RATE_LIMIT_ENABLED:
            return self.REDIS_URL
        return "memory://"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — call ``get_settings.cache_clear()`` in tests if needed."""

    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
