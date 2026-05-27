"""Typed domain exceptions.

Services raise these; only routers translate them to HTTP responses (CLAUDE.md).
The ``code`` values mirror the security-guard violation codes where relevant.
"""

from __future__ import annotations


class ServiceCatError(Exception):
    """Base class for all domain errors."""

    code: str = "SC_INTERNAL"
    status_code: int = 500

    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict[str, object] = details or {}


class NotFoundError(ServiceCatError):
    """Requested resource does not exist (in this workspace)."""

    code = "NOT_FOUND"
    status_code = 404


class ConflictError(ServiceCatError):
    """Request conflicts with current state (e.g. unique constraint)."""

    code = "CONFLICT"
    status_code = 409


class DomainValidationError(ServiceCatError):
    """Input is structurally valid but violates a business rule."""

    code = "VALIDATION"
    status_code = 422


class AuthenticationError(ServiceCatError):
    """S1 — the request is not authenticated."""

    code = "S1_UNAUTHENTICATED"
    status_code = 401


class WorkspaceIsolationError(NotFoundError):
    """S2 — cross-workspace access; surfaced as 404 to avoid leaking existence."""

    code = "S2_CROSS_WORKSPACE"


class AuthorizationError(ServiceCatError):
    """S3 — authenticated but missing the required capability."""

    code = "S3_RBAC_DENIED"
    status_code = 403


class RateLimitError(ServiceCatError):
    """S4 — request rate exceeded."""

    code = "S4_RATE_LIMITED"
    status_code = 429
