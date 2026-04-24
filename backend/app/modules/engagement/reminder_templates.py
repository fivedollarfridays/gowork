"""Reminder email templates — SOFT / MEDIUM / HARD bodies (T12.19).

Every worker-supplied field (first name, days, barrier ids) is HTML-escaped
at interpolation time. Every body includes an unsubscribe link to satisfy
CAN-SPAM (see :func:`build_unsubscribe_url`).

Kept in its own module so reminder_engine.py stays under the per-file
function limit.
"""

from __future__ import annotations

import html
import os
from dataclasses import dataclass

from app.modules.common.temporal_types import StallLevel
from app.modules.engagement.unsubscribe_tokens import sign as _sign_unsub

__all__ = [
    "RenderedEmail",
    "category_for_level",
    "render_reminder",
    "build_unsubscribe_url",
]


@dataclass(frozen=True)
class RenderedEmail:
    """Fully rendered email payload ready for transactional dispatch."""

    subject: str
    html: str
    text: str


_CATEGORY_BY_LEVEL = {
    StallLevel.SOFT: "stall_soft",
    StallLevel.MEDIUM: "stall_medium",
    StallLevel.HARD: "stall_hard",
}


def category_for_level(level: StallLevel) -> str:
    """Return the cooldown/dedup category string for a stall level."""
    try:
        return _CATEGORY_BY_LEVEL[level]
    except KeyError as exc:  # pragma: no cover - enum is closed
        raise ValueError(f"No reminder category for level: {level}") from exc


# -------------------- Template copy --------------------
#
# The three copies share structure but escalate in tone. Keeping them as
# module constants (rather than per-level helpers) preserves the function
# budget for this file.

_SUBJECT_BY_LEVEL = {
    StallLevel.SOFT: "[MontGoWork] Checking in — small step today?",
    StallLevel.MEDIUM: "[MontGoWork] It's been a week — here to help",
    StallLevel.HARD: "[MontGoWork] Let's reconnect",
}

_INTRO_BY_LEVEL = {
    StallLevel.SOFT: (
        "We noticed things have been quiet for a few days. "
        "Even one small action keeps your plan moving."
    ),
    StallLevel.MEDIUM: (
        "It's been about a week since your last logged action. "
        "Life happens — we're here to help you re-start."
    ),
    StallLevel.HARD: (
        "It's been two weeks. We'd love to reconnect and adjust "
        "your plan to what works now."
    ),
}


# -------------------- Public API --------------------


def build_unsubscribe_url(session_id: str) -> str:
    """Return the CAN-SPAM unsubscribe URL for this session.

    Uses :func:`app.modules.engagement.unsubscribe_tokens.sign` so the
    embedded token round-trips through the public unsubscribe routes
    (``GET`` and ``POST /api/engagement/unsubscribe``). The
    appointments-token signer is NOT reused — it signs appointment IDs
    with a different secret/action scheme.
    """
    host = os.environ.get("APP_HOST", "https://app.montgowork.local")
    token = _sign_unsubscribe_token(session_id)
    return f"{host}/api/engagement/unsubscribe?token={token}"


def _sign_unsubscribe_token(session_id: str) -> str:
    """Sign a single-use engagement-unsubscribe token for ``session_id``.

    Thin wrapper around :func:`unsubscribe_tokens.sign` so tests can
    monkeypatch this seam without reaching into the signer module.
    """
    return _sign_unsub(session_id)


def render_reminder(
    level: StallLevel,
    *,
    first_name: str,
    session_id: str,
    days_stalled: int,
) -> RenderedEmail:
    """Render subject + HTML + text for a stall-level reminder email."""
    safe_name = html.escape(first_name or "friend")
    days = max(int(days_stalled), 0)
    unsubscribe = build_unsubscribe_url(session_id)
    subject = _SUBJECT_BY_LEVEL[level]
    intro = _INTRO_BY_LEVEL[level]
    body_html = _html_body(safe_name, intro, days, unsubscribe)
    body_text = _text_body(first_name or "friend", intro, days, unsubscribe)
    return RenderedEmail(subject=subject, html=body_html, text=body_text)


def _html_body(
    safe_name: str, intro: str, days: int, unsubscribe: str,
) -> str:
    return (
        f"<p>Hi {safe_name},</p>"
        f"<p>{html.escape(intro)}</p>"
        f"<p>It's been {days} day(s) since your last tracked action.</p>"
        f"<p><a href=\"{html.escape(unsubscribe)}\">"
        "Unsubscribe from reminders</a></p>"
    )


def _text_body(
    name: str, intro: str, days: int, unsubscribe: str,
) -> str:
    return (
        f"Hi {name},\n\n"
        f"{intro}\n\n"
        f"It's been {days} day(s) since your last tracked action.\n\n"
        f"Unsubscribe: {unsubscribe}\n"
    )


def render_digest_wrapper(
    *,
    subject: str, html_body: str, text_body: str, session_id: str,
) -> RenderedEmail:
    """Augment a pre-composed digest with a CAN-SPAM unsubscribe footer."""
    unsubscribe = build_unsubscribe_url(session_id)
    html_out = (
        f"{html_body}"
        f"<p><a href=\"{html.escape(unsubscribe)}\">"
        "Unsubscribe from emails</a></p>"
    )
    text_out = f"{text_body}\nUnsubscribe: {unsubscribe}\n"
    return RenderedEmail(subject=subject, html=html_out, text=text_out)
