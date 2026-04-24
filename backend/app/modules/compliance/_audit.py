"""Shared audit + session-hash helpers for the compliance module (T12.36).

Kept private to the package so the public hub (``__init__``) can stay
minimal. Writes land in ``compliance_audit`` (m006) with a
SHA256-hashed session id so the audit row survives deletion of the
underlying session without leaking the id itself.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

__all__ = ["hash_session_id", "hash_actor", "write_audit"]


def hash_session_id(session_id: str) -> str:
    """SHA256 hex of the raw session id — stable audit key post-deletion."""
    return hashlib.sha256(session_id.encode("utf-8")).hexdigest()


def hash_actor(actor_token: str | None) -> str | None:
    """Hash the caller's token for the audit row; ``None`` stays ``None``."""
    if actor_token is None:
        return None
    return hashlib.sha256(actor_token.encode("utf-8")).hexdigest()


def write_audit(
    *,
    db_path: str | Path,
    session_id: str,
    action: str,
    category: str | None = None,
    actor_token: str | None = None,
    payload: dict | None = None,
    now: datetime | None = None,
) -> None:
    """Insert one row into compliance_audit. Swallows no exceptions."""
    ts = (now if now is not None else datetime.now(timezone.utc)).isoformat()
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO compliance_audit "
            "(session_id_hash, action, category, actor_token_hash, "
            "payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                hash_session_id(session_id),
                action,
                category,
                hash_actor(actor_token),
                json.dumps(payload or {}, separators=(",", ":"), sort_keys=True),
                ts,
            ),
        )
        conn.commit()
    finally:
        conn.close()
