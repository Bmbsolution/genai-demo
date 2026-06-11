"""Application configuration, loaded from GATHERLY_*-prefixed env vars."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings. Every value is overridable via the environment."""

    model_config = SettingsConfigDict(
        env_prefix="GATHERLY_",
        env_file=".env",
        extra="ignore",
    )

    # SQLite by default: zero external infra, one-command run, demo-safe. Point
    # at Postgres in production by overriding GATHERLY_DATABASE_URL.
    database_url: str = "sqlite+aiosqlite:///./gatherly.db"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    cors_allow_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"],
    )
    # Dev convenience: allow any localhost port (the Next dev server may fall
    # back to 3001+). Tighten for non-local environments.
    cors_allow_origin_regex: str = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"

    # JWT (HS256 — symmetric secret). The dev default MUST be overridden outside
    # local via GATHERLY_JWT_SECRET (rule S7: secrets only via env).
    jwt_secret: str = "dev-only-insecure-secret-change-me"  # noqa: S105
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 900  # 15 minutes
    refresh_token_ttl_seconds: int = 604800  # 7 days

    # Google Sign-In (Identity Services / ID-token flow). The client id is not a
    # secret, but lives in the environment so it's configurable per deployment.
    # Empty disables the Google button (the dev-mock fallback).
    google_client_id: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached settings singleton."""
    return Settings()
