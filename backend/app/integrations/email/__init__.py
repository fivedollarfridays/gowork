"""Email integration package (T12.2).

Public API is a single function :func:`send_transactional` that wraps
SendGrid with retry, kill-switch gating, bounce dedup, and audit logging
to the ``engagement_events`` table.
"""

from __future__ import annotations

from app.integrations.email.sendgrid_client import (
    EmailSendResult,
    send_transactional,
)

__all__ = ["send_transactional", "EmailSendResult"]
