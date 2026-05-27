"""Shared pytest fixtures, including a migrated throwaway RLS test database."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from servicecat.config import get_settings
from servicecat.main import create_app

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from sqlalchemy.engine import URL
    from sqlalchemy.ext.asyncio import AsyncSession

BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_DB_NAME = "servicecat_test"


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """An httpx client wired directly to the ASGI app (no network)."""
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def redis_client() -> AsyncIterator[Redis]:
    """A real Redis connection (the local stack on :6380), closed after the test."""
    client = Redis.from_url(get_settings().redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


async def _admin_execute(admin_url: URL, statements: list[str]) -> None:
    """Run maintenance statements (CREATE/DROP DATABASE) in autocommit."""
    conn = await asyncpg.connect(
        user=admin_url.username,
        password=admin_url.password,
        host=admin_url.host,
        port=admin_url.port,
        database=admin_url.database,
    )
    try:
        for stmt in statements:
            await conn.execute(stmt)
    finally:
        await conn.close()


def _run_alembic(test_url: URL, *args: str) -> None:
    env = {
        **os.environ,
        "SERVICECAT_DATABASE_URL": test_url.render_as_string(hide_password=False),
    }
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=str(BACKEND_DIR),
        env=env,
        check=True,
        capture_output=True,
    )


@pytest.fixture(scope="session")
def rls_database_url() -> Iterator[str]:
    """Create a fresh ``servicecat_test`` DB, migrate it, drop it after.

    Tearing down with ``alembic downgrade base`` also asserts the migration is
    reversible (the subprocess raises if downgrade fails).
    """
    admin_url = make_url(get_settings().database_url)
    test_url = admin_url.set(database=TEST_DB_NAME)
    terminate = (
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        f"WHERE datname = '{TEST_DB_NAME}' AND pid <> pg_backend_pid()"
    )
    asyncio.run(
        _admin_execute(
            admin_url,
            [
                terminate,
                f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"',
                f'CREATE DATABASE "{TEST_DB_NAME}"',
            ],
        )
    )
    _run_alembic(test_url, "upgrade", "head")
    try:
        yield test_url.render_as_string(hide_password=False)
    finally:
        _run_alembic(test_url, "downgrade", "base")
        asyncio.run(
            _admin_execute(admin_url, [terminate, f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"'])
        )


@pytest.fixture
async def rls_sessionmaker(
    rls_database_url: str,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """A session factory on the test DB, with tables truncated per test."""
    engine = create_async_engine(rls_database_url)
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE workspace_memberships, workspaces, users CASCADE"))
    try:
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        await engine.dispose()
