"""Shared pytest fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from httpx import ASGITransport, AsyncClient

from servicecat.main import create_app

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """An httpx client wired directly to the ASGI app (no network)."""
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
