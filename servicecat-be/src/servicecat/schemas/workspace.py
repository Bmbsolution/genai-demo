"""Workspace response schema."""

from __future__ import annotations

import uuid

from servicecat.schemas.base import ServiceCatBaseModel


class WorkspaceResponse(ServiceCatBaseModel):
    id: uuid.UUID
    name: str
    slug: str
    role: str
