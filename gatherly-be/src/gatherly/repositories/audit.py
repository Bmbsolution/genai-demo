"""Data access for the append-only audit log (S5).

Exposes only ``record`` — no update or delete — so the log stays append-only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from gatherly.models import AuditLog


class AuditLogRepository:
    """Appends entries to the audit log."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def record(self, entry: AuditLog) -> None:
        self._db.add(entry)
        await self._db.flush()
