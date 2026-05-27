"""Audit log response schema."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import field_validator

from servicecat.schemas.base import ServiceCatBaseModel


class AuditLogResponse(ServiceCatBaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    actor_id: uuid.UUID
    action: str
    resource_type: str
    resource_id: uuid.UUID | None
    payload: dict[str, Any] | None
    ip: str | None
    user_agent: str | None
    created_at: datetime

    @field_validator("ip", mode="before")
    @classmethod
    def _stringify_ip(cls, value: object) -> str | None:
        # asyncpg returns INET columns as ipaddress objects, not str.
        return None if value is None else str(value)
