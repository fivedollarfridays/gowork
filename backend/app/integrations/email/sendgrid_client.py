"""SendGrid transactional email sender (T12.2).

Public entry point: :func:`send_transactional` — kill-switch gated,
hard-bounce deduped, retry with exponential backoff, audit-logged to
``engagement_events``, structured logging via stdlib ``logging``.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Literal

from app.core import feature_flags
from app.integrations.email.core import (
    EmailSendResult,
    build_payload,
    has_recent_hard_bounce,
    log_engagement_event,
    resolve_db_path,
)

__all__ = ["send_transactional", "EmailSendResult"]

logger = logging.getLogger("app.integrations.email")

_MAX_ATTEMPTS = 3
_BACKOFF_SECONDS = (1, 2, 4)
_FEATURE_FLAG = "EMAIL_SEND_ENABLED"

EmailCategory = Literal[
    "digest",
    "reminder",
    "stall_alert",
    "appointment_confirmation",
    "appointment_reminder",
]


# -------------------- Public API --------------------


def send_transactional(
    to: str,
    subject: str,
    html: str,
    text_fallback: str,
    category: EmailCategory,
    *,
    session_id: str | None = None,
    db_path: str | Path | None = None,
) -> EmailSendResult:
    """Send a transactional email via SendGrid with retry + audit logging."""
    resolved_db = resolve_db_path(db_path)
    skip = _check_preflight_skips(to, category, resolved_db)
    if skip is not None:
        return skip
    payload = build_payload(
        to=to, subject=subject, html=html,
        text_fallback=text_fallback, category=category,
    )
    return _send_with_retries(
        payload=payload, to=to, category=category,
        session_id=session_id, db_path=resolved_db,
    )


def _check_preflight_skips(
    to: str, category: str, db_path: Path | None
) -> EmailSendResult | None:
    """Return an early-skip result (or None if the send may proceed)."""
    if not feature_flags.is_enabled(_FEATURE_FLAG, default=True):
        logger.info(
            "email send skipped (kill switch): to=%s category=%s", to, category
        )
        return EmailSendResult(
            success=False, message_id=None, attempt_count=0,
            skipped_reason="kill_switch",
        )
    if has_recent_hard_bounce(db_path, to):
        logger.info(
            "email send skipped (recent hard bounce): to=%s category=%s",
            to, category,
        )
        return EmailSendResult(
            success=False, message_id=None, attempt_count=0,
            skipped_reason="recent_hard_bounce",
        )
    return None


# -------------------- Retry loop --------------------


def _send_with_retries(
    *,
    payload: dict[str, Any],
    to: str,
    category: str,
    session_id: str | None,
    db_path: Path | None,
) -> EmailSendResult:
    """Run up to ``_MAX_ATTEMPTS`` send attempts with exponential backoff."""
    client = _build_client()
    last_error: str | None = None
    message_id: str | None = None

    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            result = client.send(payload)
        except Exception as exc:  # noqa: BLE001 - provider exception is unknown
            last_error = f"{type(exc).__name__}: {exc}"
            _log_retry_or_final(attempt, to, category, last_error)
            if attempt < _MAX_ATTEMPTS:
                time.sleep(_BACKOFF_SECONDS[attempt - 1])
            continue
        message_id = result.get("message_id")
        logger.info(
            "email sent: to=%s category=%s attempt=%d message_id=%s",
            to, category, attempt, message_id,
        )
        _audit_success(db_path, session_id, to, category, attempt, message_id)
        return EmailSendResult(
            success=True, message_id=message_id, attempt_count=attempt,
            skipped_reason=None,
        )

    _audit_failure(db_path, session_id, to, category, last_error)
    return EmailSendResult(
        success=False, message_id=None, attempt_count=_MAX_ATTEMPTS,
        skipped_reason=None,
    )


def _log_retry_or_final(
    attempt: int, to: str, category: str, error: str
) -> None:
    """Emit WARNING for retryable failure, ERROR for the final attempt."""
    if attempt < _MAX_ATTEMPTS:
        logger.warning(
            "email send failed (will retry): to=%s category=%s "
            "attempt=%d error=%s",
            to, category, attempt, error,
        )
    else:
        logger.error(
            "email send failed (final): to=%s category=%s attempt=%d error=%s",
            to, category, attempt, error,
        )


# -------------------- Audit helpers --------------------


def _audit_success(
    db_path: Path | None,
    session_id: str | None,
    to: str,
    category: str,
    attempts: int,
    message_id: str | None,
) -> None:
    log_engagement_event(
        db_path,
        session_id=session_id,
        category="email_sent",
        payload={
            "to": to, "category": category,
            "attempts": attempts, "message_id": message_id,
        },
    )


def _audit_failure(
    db_path: Path | None,
    session_id: str | None,
    to: str,
    category: str,
    error: str | None,
) -> None:
    log_engagement_event(
        db_path,
        session_id=session_id,
        category="email_send_failed",
        payload={
            "to": to, "category": category,
            "attempts": _MAX_ATTEMPTS, "error": error or "unknown",
        },
    )


# -------------------- Client factory --------------------


def _build_client() -> Any:
    """Return a concrete SendGrid client.

    Tests monkeypatch this function to substitute a mock. The real
    implementation lives in :mod:`.provider`.
    """
    from app.integrations.email.provider import RealSendGridClient

    return RealSendGridClient(api_key=os.environ.get("SENDGRID_API_KEY", ""))
