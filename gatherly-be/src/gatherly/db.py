"""Async database engine, session factory, and schema initialisation."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from gatherly.config import get_settings
from gatherly.models import Base

if TYPE_CHECKING:
    from sqlalchemy.engine.interfaces import DBAPIConnection
    from sqlalchemy.pool import ConnectionPoolEntry


def enable_sqlite_foreign_keys(engine: AsyncEngine) -> None:
    """Turn on SQLite FK enforcement so ``ON DELETE CASCADE`` actually cascades.

    SQLite ships with foreign keys OFF per connection; Postgres enforces them
    natively. Call this on any SQLite engine (app + tests) so deleting an
    account removes its events and guests.
    """

    @event.listens_for(engine.sync_engine, "connect")
    def _set_pragma(dbapi_conn: DBAPIConnection, _: ConnectionPoolEntry) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Return the process-wide async engine."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    if settings.database_url.startswith("sqlite"):
        enable_sqlite_foreign_keys(engine)
    return engine


@lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return the process-wide async session factory."""
    return async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    """Create all tables if they don't exist (SQLite demo — no migrations)."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
