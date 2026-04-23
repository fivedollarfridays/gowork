"""SQLite write helpers for the SendGrid Event Webhook route (T12.2a).

Extracted from :mod:`app.routes.sendgrid_webhook` so the route file stays
under the architecture 12-functions-per-file limit. Each helper is
best-effort: missing DB / table / session FK failures are swallowed and
logged — the webhook must still return 204 so SendGrid does not retry.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("app.routes.sendgrid_webhook.db")

_SENDGRID_INSERT = (
    "INSERT INTO sendgrid_events "
    "(event_type, email, message_id, reason, raw_payload_json, created_at) "
    "VALUES (?, ?, ?, ?, ?, ?)"
)

_ENGAGEMENT_INSERT = (
    "INSERT INTO engagement_events "
    "(session_id, category, payload_json, created_at) "
    "VALUES (?, ?, ?, ?)"
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def insert_sendgrid_event(
    db_path: Path | None,
    *,
    event_type: str,
    event: dict[str, Any],
) -> None:
    """Append an event to ``sendgrid_events``. Best-effort."""
    if db_path is None or not db_path.exists():
        return
    email = event.get("email")
    message_id = event.get("sg_message_id")
    reason = event.get("reason")
    raw = json.dumps(event, sort_keys=True)
    try:
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                _SENDGRID_INSERT,
                (event_type, email, message_id, reason, raw, _now_iso()),
            )
            conn.commit()
        finally:
            conn.close()
    except sqlite3.DatabaseError:
        logger.exception("Failed to insert sendgrid_events row")


def log_reminders_auto_disabled(
    db_path: Path | None, *, session_id: str, reason: str,
) -> None:
    """Append a ``reminders_auto_disabled`` audit row. Best-effort.

    This is the signal downstream reminder code must respect until the
    ``sessions.reminders_enabled`` column lands (S12b).
    """
    if db_path is None or not db_path.exists():
        return
    payload = json.dumps(
        {"session_id": session_id, "reason": reason}, sort_keys=True,
    )
    try:
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                _ENGAGEMENT_INSERT,
                (session_id, "reminders_auto_disabled", payload, _now_iso()),
            )
            conn.commit()
        finally:
            conn.close()
    except sqlite3.DatabaseError:
        logger.exception("Failed to insert reminders_auto_disabled audit row")
