"""Smoke test: the app boots and /health responds with the success envelope."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpx import AsyncClient


async def test_health_ok(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["data"]["status"] == "ok"
