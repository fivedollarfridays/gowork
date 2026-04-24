"""DB read helpers for ``scripts.nightly_digest`` — keeps the orchestrator's
import surface narrow so the project's per-file import ceiling holds.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path


def collect_active_sessions_for_city(
    city: str, db_path: Path, now: datetime,
) -> list[str]:
    """Return session IDs active at ``now`` and tagged to ``city``.

    "Active" = ``expires_at`` > now OR NULL. "Tagged to city" = has at
    least one ``outcomes_records`` row whose ``payload_json.city == city``.
    See ``scripts.nightly_digest``'s module docstring for the
    scope-enforcement rationale.
    """
    now_iso = now.isoformat()
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT DISTINCT s.id FROM sessions s "
            "JOIN outcomes_records o ON o.session_id = s.id "
            "WHERE (s.expires_at IS NULL OR s.expires_at > ?) "
            "AND json_extract(o.payload_json, '$.city') = ?",
            (now_iso, city),
        ).fetchall()
    finally:
        conn.close()
    return [r[0] for r in rows]


def resolve_session_email(session_id: str, db_path: Path) -> str | None:
    """Pull ``profile.email`` from the sessions row; ``None`` if missing."""
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT profile FROM sessions WHERE id = ?", (session_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row or not row[0]:
        return None
    try:
        profile = json.loads(row[0])
    except (json.JSONDecodeError, TypeError):
        return None
    email = profile.get("email") if isinstance(profile, dict) else None
    if isinstance(email, str) and email.strip():
        return email.strip()
    return None


__all__ = ["collect_active_sessions_for_city", "resolve_session_email"]
