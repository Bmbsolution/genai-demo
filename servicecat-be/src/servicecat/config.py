"""Application configuration, loaded from SERVICECAT_*-prefixed env vars."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings. Every value is overridable via the environment."""

    model_config = SettingsConfigDict(
        env_prefix="SERVICECAT_",
        env_file=".env",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://servicecat:servicecat@localhost:5440/servicecat"
    redis_url: str = "redis://localhost:6380/0"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached settings singleton."""
    return Settings()
