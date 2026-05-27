"""Lazily-loaded RS256 JWT keys, read from the configured PEM files.

Exposed as plain functions so they can be used as FastAPI dependencies and
overridden in tests (``app.dependency_overrides``) without touching the cache.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from servicecat.config import get_settings


@lru_cache(maxsize=1)
def _read_pem(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def get_jwt_private_key() -> str:
    """Return the RS256 private signing key (PEM)."""
    return _read_pem(get_settings().jwt_private_key_path)


def get_jwt_public_key() -> str:
    """Return the RS256 public verification key (PEM)."""
    return _read_pem(get_settings().jwt_public_key_path)
