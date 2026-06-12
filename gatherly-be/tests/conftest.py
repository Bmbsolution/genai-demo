"""Shared test fixtures: in-memory SQLite + an ASGI client with overridden deps."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from gatherly import rate_limit
from gatherly.db import enable_sqlite_foreign_keys
from gatherly.deps import get_db
from gatherly.main import create_app
from gatherly.models import Base, User, UserPlan
from gatherly.rbac import Role
from gatherly.security import hash_password
from gatherly.token_store import get_revocation_store

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncEngine

DEFAULT_PASSWORD = "pw-secret-123"


@pytest_asyncio.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    """A single shared in-memory SQLite engine (StaticPool) with the schema built."""
    eng = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    enable_sqlite_foreign_keys(eng)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def sessions(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(autouse=True)
def _reset_process_state() -> None:
    """The rate limiter and revocation store are process singletons — reset them
    between tests so cases don't bleed into each other."""
    rate_limit.reset()
    get_revocation_store()._revoked.clear()


@pytest_asyncio.fixture
async def client(sessions: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncClient]:
    app = create_app()

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        async with sessions() as session, session.begin():
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


async def create_host(
    sessions: async_sessionmaker[AsyncSession],
    *,
    email: str,
    password: str = DEFAULT_PASSWORD,
    role: Role = Role.ADMIN,
    plan: UserPlan = UserPlan.PRO,
) -> User:
    """Insert a host directly so tests can then log in through the real flow.

    Defaults to Pro so feature tests aren't tripped by free-tier caps; billing
    tests pass ``plan=UserPlan.FREE`` to exercise the limits.
    """
    user = User(
        email=email,
        display_name="Test Host",
        role=role.value,
        hashed_password=hash_password(password),
        plan=plan.value,
    )
    async with sessions() as session, session.begin():
        session.add(user)
    return user


async def login(
    client: AsyncClient, email: str, password: str = DEFAULT_PASSWORD
) -> dict[str, str]:
    """Log in and return an Authorization header dict."""
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
