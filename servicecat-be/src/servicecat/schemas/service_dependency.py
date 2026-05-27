"""Service dependency request/response schemas."""

from __future__ import annotations

import uuid

from servicecat.models import DependencyCriticality, DependencyDirection
from servicecat.schemas.base import ServiceCatBaseModel


class ServiceDependencyCreateRequest(ServiceCatBaseModel):
    depends_on_service_id: uuid.UUID
    criticality: DependencyCriticality
    direction: DependencyDirection


class ServiceDependencyResponse(ServiceCatBaseModel):
    id: uuid.UUID
    service_id: uuid.UUID
    depends_on_service_id: uuid.UUID
    criticality: str
    direction: str
    depth: int
