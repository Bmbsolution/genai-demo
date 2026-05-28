"""Application configuration, loaded from SERVICECAT_*-prefixed env vars."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
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
    cors_allow_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"],
    )
    # Dev convenience: allow any localhost port (the Next dev server may fall
    # back to 3001+ if 3000 is taken). Tighten for non-local environments.
    cors_allow_origin_regex: str = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"

    # JWT (RS256). Keys are PEM files outside version control; generate a local
    # dev pair into ./secrets/ and never commit real keys (rule S7).
    jwt_algorithm: str = "RS256"
    jwt_private_key_path: str = "secrets/jwt_private.pem"
    jwt_public_key_path: str = "secrets/jwt_public.pem"
    access_token_ttl_seconds: int = 900  # 15 minutes
    refresh_token_ttl_seconds: int = 604800  # 7 days


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached settings singleton."""
    return Settings()
