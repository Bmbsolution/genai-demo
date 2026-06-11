"""Typed domain exceptions.

Services raise these; only routers translate them to HTTP responses. The
``code`` values mirror the security-guard violation codes where relevant.
"""

from __future__ import annotations


class GatherlyError(Exception):
    """Base class for all domain errors."""

    code: str = "GA_INTERNAL"
    status_code: int = 500

    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict[str, object] = details or {}


class NotFoundError(GatherlyError):
    """Requested resource does not exist (or isn't visible to the caller)."""

    code = "NOT_FOUND"
    status_code = 404


class ConflictError(GatherlyError):
    """Request conflicts with current state (e.g. unique constraint)."""

    code = "CONFLICT"
    status_code = 409


class DomainValidationError(GatherlyError):
    """Input is structurally valid but violates a business rule."""

    code = "VALIDATION"
    status_code = 422


class AuthenticationError(GatherlyError):
    """S1 — the request is not authenticated."""

    code = "S1_UNAUTHENTICATED"
    status_code = 401


class OwnershipError(NotFoundError):
    """S2 — accessing a resource the caller doesn't own; surfaced as 404 so we
    never leak whether someone else's event/guest exists."""

    code = "S2_NOT_OWNER"


class AuthorizationError(GatherlyError):
    """S3 — authenticated but missing the required capability."""

    code = "S3_RBAC_DENIED"
    status_code = 403


class RateLimitError(GatherlyError):
    """S4 — request rate exceeded."""

    code = "S4_RATE_LIMITED"
    status_code = 429
