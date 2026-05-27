"""Shared httpx.AsyncClient. Rule S8: all external calls go through this, 30s cap."""

from __future__ import annotations

from functools import lru_cache

import httpx

DEFAULT_TIMEOUT_SECONDS = 30.0


@lru_cache(maxsize=1)
def get_http_client() -> httpx.AsyncClient:
    """Return the process-wide async HTTP client with the mandatory timeout."""
    return httpx.AsyncClient(timeout=httpx.Timeout(DEFAULT_TIMEOUT_SECONDS))


async def close_http_client() -> None:
    """Close and reset the shared client (called on application shutdown)."""
    client = get_http_client()
    await client.aclose()
    get_http_client.cache_clear()
