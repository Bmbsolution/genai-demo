"""Finding response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from servicecat.schemas.base import ServiceCatBaseModel
from servicecat.schemas.service import PageMeta


class FindingResponse(ServiceCatBaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    service_id: uuid.UUID
    criterion_id: str
    severity: str
    remediation: str
    evidence: dict[str, Any] | None
    auto_fixable: bool
    created_at: datetime


class FindingListResponse(ServiceCatBaseModel):
    data: list[FindingResponse]
    meta: PageMeta
