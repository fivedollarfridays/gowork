"""Advisor-note spoke for reminder_engine (T12.31).

Extracted from :mod:`app.modules.engagement.reminder_engine` to keep
that module under the architecture 300-line limit. Provides the
public :func:`send_advisor_note` — a single-email send path that
reuses the engine's dispatch helpers but skips the cooldown check
(advisor notes are human-authored and rate-limited at the route
layer, 3/hour per advisor).

The opt-out / kill-switch preflight is preserved: a worker who opted
out of reminders (via hard bounce or explicit request) never
receives an advisor note through this path.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.core import feature_flags

__all__ = ["send_advisor_note"]

_ADVISOR_NOTE_CATEGORY = "advisor_note"
_KILL_SWITCH_FLAG = "EMAIL_SEND_ENABLED"


def _render_advisor_email(first_name: str, message: str):
    """Build the Rendered* email for an advisor personal note."""
    from app.modules.engagement.reminder_engine import (  # noqa: WPS433
        RenderedEmail,
    )
    body_text = message.strip()
    subject = f"A personal note from your advisor, {first_name}"
    body_html = (
        f"<p>Hi {first_name},</p><p>{body_text}</p>"
        "<p>— Your MontGoWork case-manager team</p>"
    )
    return RenderedEmail(subject=subject, html=body_html, text=body_text)


def send_advisor_note(
    session_id: str,
    message: str,
    *,
    db_path: str | Path,
    now: datetime | None = None,
):
    """Dispatch an advisor-authored personal note to the worker.

    Returns the same
    :class:`app.modules.engagement.reminder_engine.ReminderDispatchResult`
    shape as the rest of the engine. Imports are done inline to avoid
    a circular dependency (the engine's public ``__all__`` re-exports
    this function).
    """
    from app.modules.engagement.reminder_engine import (  # noqa: WPS433
        _dispatch,
        _is_reminders_auto_disabled,
        _load_profile,
        _skip,
    )

    if not feature_flags.is_enabled(_KILL_SWITCH_FLAG, default=True):
        return _skip("kill_switch", _ADVISOR_NOTE_CATEGORY)
    if _is_reminders_auto_disabled(db_path, session_id):
        return _skip("reminders_disabled", _ADVISOR_NOTE_CATEGORY)
    email, first_name = _load_profile(db_path, session_id)
    if email is None:
        return _skip("no_email", _ADVISOR_NOTE_CATEGORY)
    rendered = _render_advisor_email(first_name, message)
    return _dispatch(
        to_email=email, session_id=session_id, rendered=rendered,
        category=_ADVISOR_NOTE_CATEGORY, stall_level_value=None,
        db_path=db_path, now=now,
    )
