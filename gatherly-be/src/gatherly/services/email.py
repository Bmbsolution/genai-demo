"""Outbound email — a thin, pluggable sender.

Gatherly sends invitation and reminder emails. Real delivery needs an SMTP/API
provider with secrets we don't ship in the demo, so the default backend logs
each message instead of sending it. Production overrides the backend via
``GATHERLY_EMAIL_BACKEND`` once a provider's credentials are wired in — every
call site stays identical.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger("gatherly.email")


@dataclass(frozen=True, slots=True)
class EmailMessage:
    """One outbound email."""

    to: str
    subject: str
    body: str


class EmailSender(Protocol):
    """Anything that can deliver an :class:`EmailMessage`."""

    async def send(self, message: EmailMessage) -> None:
        """Deliver ``message`` (or raise on hard failure)."""
        ...


class ConsoleEmailSender:
    """Dev/demo backend: log the email rather than deliver it.

    Keeps the full send pipeline (audit, rate limit, recipient selection) real
    and exercisable without a provider or secrets.
    """

    async def send(self, message: EmailMessage) -> None:
        logger.info("email.send to=%s subject=%s", message.to, message.subject)


def get_email_sender() -> EmailSender:
    """Return the configured sender. Console-only until a provider is wired in."""
    return ConsoleEmailSender()
