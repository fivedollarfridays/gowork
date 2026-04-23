"""Helpers for the email integration (T12.2).

Extracted from :mod:`app.integrations.email.sendgrid_client` to keep the
public module under the architecture-rule 15-function limit.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.core.config import get_settings

# -------------------- Dataclass --------------------


@dataclass(frozen=True)
class EmailSendResult:
    """Outcome of a :func:`send_transactional` call."""

    success: bool
    message_id: str | None
    attempt_count: int
    skipped_reason: str | None  # "kill_switch" | "recent_hard_bounce" | None


# -------------------- DB path resolution --------------------


def resolve_db_path(override: str | Path | None) -> Path | None:
    """Return a Path to the sqlite DB or None if unresolvable.

    Explicit override wins. Otherwise fall back to the app settings
    ``database_url`` (sqlite+aiosqlite:///path.db form).
    """
    if override is not None:
        return Path(override)
    try:
        db_url = get_settings().database_url
    except Exception:
        return None
    marker = ":///"
    idx = db_url.find(marker)
    if idx == -1:
        return None
    raw = db_url[idx + len(marker):]
    return Path(raw) if raw else None


# -------------------- Bounce dedup --------------------


_BOUNCE_WINDOW_DAYS = 7
_BOUNCE_QUERY = (
    "SELECT 1 FROM sendgrid_events "
    "WHERE event_type = 'bounce' AND email = ? AND created_at >= ? "
    "LIMIT 1"
)


def has_recent_hard_bounce(db_path: Path | None, email: str) -> bool:
    """Return True if a hard bounce for ``email`` exists in the last 7 days.

    Missing DB or missing ``sendgrid_events`` table is treated as "no bounce
    on record" — the caller proceeds with the send.
    """
    if db_path is None or not db_path.exists():
        return False
    cutoff = (
        datetime.now(timezone.utc) - timedelta(days=_BOUNCE_WINDOW_DAYS)
    ).isoformat()
    try:
        conn = sqlite3.connect(db_path)
        try:
            row = conn.execute(_BOUNCE_QUERY, (email, cutoff)).fetchone()
        finally:
            conn.close()
    except sqlite3.DatabaseError:
        return False
    return row is not None


# -------------------- Engagement audit --------------------


_ENGAGEMENT_INSERT = (
    "INSERT INTO engagement_events "
    "(session_id, category, payload_json, created_at) "
    "VALUES (?, ?, ?, ?)"
)


def log_engagement_event(
    db_path: Path | None,
    *,
    session_id: str | None,
    category: str,
    payload: dict[str, Any],
) -> None:
    """Append a row to ``engagement_events``. Best-effort; swallows DB errors.

    If ``session_id`` is None (no session context) or the DB cannot be
    reached, we skip the write silently — the caller has already emitted a
    structured log line elsewhere.
    """
    if db_path is None or session_id is None or not db_path.exists():
        return
    ts = datetime.now(timezone.utc).isoformat()
    try:
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                _ENGAGEMENT_INSERT,
                (session_id, category, json.dumps(payload), ts),
            )
            conn.commit()
        finally:
            conn.close()
    except sqlite3.DatabaseError:
        return


# -------------------- Payload building --------------------


def build_payload(
    *,
    to: str,
    subject: str,
    html: str,
    text_fallback: str,
    category: str,
) -> dict[str, Any]:
    """Construct the SendGrid mail payload dict used by both real and mock."""
    return {
        "to": to,
        "subject": subject,
        "html": html,
        "text": text_fallback,
        "categories": [category],
    }
