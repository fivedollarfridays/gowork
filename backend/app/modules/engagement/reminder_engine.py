"""Reminder + digest dispatch engine (T12.19, S12b).

Single send path for every outbound engagement email:
    * stall reminders (SOFT/MEDIUM/HARD) via :func:`send_reminder`
    * daily digest wrap via :func:`send_digest`

Both go through :mod:`cooldown` for (session_id, category) dedup before
hitting SendGrid, and both record a ``reminder_cooldowns`` row + an
``engagement_events`` audit row after a successful send.

Opt-out handling
----------------
Sessions with an ``engagement_events`` row of category
``reminders_auto_disabled`` (set either by worker opt-out or by the
T12.2a hard-bounce handler) are skipped without contacting SendGrid.
If ``sessions.reminders_enabled`` ever lands as a real column the same
check can short-circuit there too — for now the schema has no such
column (m001 / m002 both checked).
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.core import feature_flags
from app.integrations.email.core import (
    EmailSendResult,
    log_engagement_event,
    resolve_db_path,
)
from app.integrations.email.sendgrid_client import send_transactional
from app.modules.common.temporal_types import StallLevel
from app.modules.engagement import _advisor_note, _reminder_status

send_advisor_note = _advisor_note.send_advisor_note
nightly_status = _reminder_status.nightly_status
from app.modules.engagement.cooldown import (
    check_cooldown,
    record_send,
)
from app.modules.engagement.reminder_templates import (
    RenderedEmail,
    category_for_level,
    render_digest_wrapper,
    render_reminder,
)

__all__ = [
    "ReminderDispatchResult", "nightly_status",
    "send_advisor_note", "send_digest", "send_reminder",
]

logger = logging.getLogger("app.modules.engagement.reminder_engine")

_DIGEST_CATEGORY = "digest"
_KILL_SWITCH_FLAG = "EMAIL_SEND_ENABLED"


@dataclass(frozen=True)
class ReminderDispatchResult:
    """Outcome of a :func:`send_reminder` / :func:`send_digest` call."""

    success: bool
    skipped_reason: str | None  # cooldown | reminders_disabled | kill_switch | no_email
    category: str
    message_id: str | None


# -------------------- Helpers --------------------


def _skip(reason: str, category: str) -> ReminderDispatchResult:
    return ReminderDispatchResult(
        success=False, skipped_reason=reason,
        category=category, message_id=None,
    )


def _is_reminders_auto_disabled(
    db_path: str | Path, session_id: str,
) -> bool:
    """Return True when an engagement_events opt-out row exists for the session."""
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT 1 FROM engagement_events "
            "WHERE session_id = ? AND category = 'reminders_auto_disabled' "
            "LIMIT 1",
            (session_id,),
        ).fetchone()
    finally:
        conn.close()
    return row is not None


def _load_profile(
    db_path: str | Path, session_id: str,
) -> tuple[str | None, str]:
    """Return (email, first_name) from sessions.profile. Missing email → None."""
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT profile FROM sessions WHERE id = ?", (session_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row or not row[0]:
        return None, "friend"
    try:
        profile = json.loads(row[0])
    except (json.JSONDecodeError, TypeError):
        return None, "friend"
    if not isinstance(profile, dict):
        return None, "friend"
    email = profile.get("email")
    first_name = profile.get("first_name") or "friend"
    clean_email = email.strip() if isinstance(email, str) and email.strip() else None
    return clean_email, first_name


def _days_stalled(
    db_path: str | Path, session_id: str, now: datetime | None,
) -> int:
    """Best-effort days_stalled read using the stall detector."""
    from app.modules.engagement.stall_detector import compute_stall_for_session

    try:
        stalled = compute_stall_for_session(
            session_id, db_path=db_path, now=now,
        )
    except Exception:  # noqa: BLE001 — detector errors shouldn't block a send
        return 0
    return int(getattr(stalled, "days_stalled", 0) or 0)


def _record_success_audit(
    *,
    session_id: str,
    category: str,
    stall_level_value: str | None,
    message_id: str | None,
    db_path: str | Path,
    now: datetime | None,
) -> None:
    """Persist cooldown row + engagement_events audit entry for a success."""
    record_send(
        session_id, category, stall_level_value,
        db_path=db_path, now=now,
    )
    audit_category = (
        "digest_sent" if category == _DIGEST_CATEGORY else "reminder_sent"
    )
    log_engagement_event(
        resolve_db_path(db_path),
        session_id=session_id,
        category=audit_category,
        payload={
            "category": category, "stall_level": stall_level_value,
            "message_id": message_id,
        },
    )


def _dispatch(
    *,
    to_email: str,
    session_id: str,
    rendered: RenderedEmail,
    category: str,
    stall_level_value: str | None,
    db_path: str | Path,
    now: datetime | None,
) -> ReminderDispatchResult:
    """Call SendGrid, then record cooldown + audit. Shared by reminder and digest."""
    result: EmailSendResult = send_transactional(
        to_email, rendered.subject, rendered.html, rendered.text,
        category,  # type: ignore[arg-type] - Literal narrowed by caller
        session_id=session_id, db_path=db_path,
    )
    if result.skipped_reason == "kill_switch":
        return _skip("kill_switch", category)
    if not result.success:
        return ReminderDispatchResult(
            success=False, skipped_reason=result.skipped_reason,
            category=category, message_id=None,
        )
    _record_success_audit(
        session_id=session_id, category=category,
        stall_level_value=stall_level_value,
        message_id=result.message_id, db_path=db_path, now=now,
    )
    return ReminderDispatchResult(
        success=True, skipped_reason=None,
        category=category, message_id=result.message_id,
    )


# -------------------- Public API --------------------


def _preflight(
    session_id: str, category: str, *, db_path: str | Path, now: datetime | None,
) -> str | None:
    """Return a skip reason (kill_switch / reminders_disabled / cooldown) or None."""
    if not feature_flags.is_enabled(_KILL_SWITCH_FLAG, default=True):
        return "kill_switch"
    if _is_reminders_auto_disabled(db_path, session_id):
        logger.info(
            "email skipped (reminders auto-disabled): session_id=%s category=%s",
            session_id, category,
        )
        return "reminders_disabled"
    if not check_cooldown(session_id, category, db_path=db_path, now=now):
        return "cooldown"
    return None


def send_reminder(
    session_id: str,
    stall_level: StallLevel,
    *,
    db_path: str | Path,
    now: datetime | None = None,
) -> ReminderDispatchResult:
    """Dispatch a stall reminder email for ``session_id`` at ``stall_level``."""
    category = category_for_level(stall_level)
    skip_reason = _preflight(session_id, category, db_path=db_path, now=now)
    if skip_reason is not None:
        return _skip(skip_reason, category)
    email, first_name = _load_profile(db_path, session_id)
    if email is None:
        return _skip("no_email", category)
    rendered = render_reminder(
        stall_level,
        first_name=first_name,
        session_id=session_id,
        days_stalled=_days_stalled(db_path, session_id, now),
    )
    return _dispatch(
        to_email=email,
        session_id=session_id,
        rendered=rendered,
        category=category,
        stall_level_value=stall_level.value,
        db_path=db_path,
        now=now,
    )


def send_digest(
    session_id: str,
    to_email: str,
    subject: str,
    html: str,
    text: str,
    *,
    db_path: str | Path,
    now: datetime | None = None,
) -> ReminderDispatchResult:
    """Dispatch a pre-composed digest through the cooldown-gated send path."""
    skip_reason = _preflight(
        session_id, _DIGEST_CATEGORY, db_path=db_path, now=now,
    )
    if skip_reason is not None:
        return _skip(skip_reason, _DIGEST_CATEGORY)
    rendered = render_digest_wrapper(
        subject=subject, html_body=html,
        text_body=text, session_id=session_id,
    )
    return _dispatch(
        to_email=to_email,
        session_id=session_id,
        rendered=rendered,
        category=_DIGEST_CATEGORY,
        stall_level_value=None,
        db_path=db_path,
        now=now,
    )
