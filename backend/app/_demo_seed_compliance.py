"""Compliance-state spoke for the QC demo seed (T13.2).

Plants per-session ``feedback_tokens`` (active + expired) and a small
``compliance_audit`` trail. Idempotent on a populated DB.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta


__all__ = ["seed_feedback_tokens", "seed_compliance_audit"]


def _slot_token(session_id: str, slot: str) -> str:
    digest = hashlib.sha256(f"qc:{session_id}:{slot}".encode()).hexdigest()
    return f"demo-{slot}-{digest[:24]}"


def _slot_hash(session_id: str, slot: str) -> str:
    return hashlib.sha256(f"qc:{session_id}:{slot}".encode()).hexdigest()


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def seed_feedback_tokens(
    conn: sqlite3.Connection, session_id: str, now: datetime,
) -> None:
    """Plant one active + one expired feedback_tokens row per session."""
    active_token = _slot_token(session_id, "feedback-active")
    expired_token = _slot_token(session_id, "feedback-expired")
    conn.execute(
        "INSERT OR IGNORE INTO feedback_tokens "
        "(token, session_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (
            active_token, session_id,
            _iso(now - timedelta(days=2)),
            _iso(now + timedelta(days=14)),
        ),
    )
    conn.execute(
        "INSERT OR IGNORE INTO feedback_tokens "
        "(token, session_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (
            expired_token, session_id,
            _iso(now - timedelta(days=45)),
            _iso(now - timedelta(days=1)),
        ),
    )


_AUDIT_ACTIONS: tuple[str, ...] = ("export_requested", "export_downloaded")


def seed_compliance_audit(
    conn: sqlite3.Connection, session_id: str, now: datetime,
) -> None:
    """Plant a small audit trail per session.

    Two rows per session: ``export_requested`` then ``export_downloaded``.
    Hashed session id matches what :mod:`app.modules.compliance._audit`
    would write.
    """
    sid_hash = hashlib.sha256(session_id.encode("utf-8")).hexdigest()
    actor_hash = _slot_hash(session_id, "audit-actor")
    for offset, action in enumerate(_AUDIT_ACTIONS):
        ts = _iso(now - timedelta(days=7 - offset))
        existing = conn.execute(
            "SELECT 1 FROM compliance_audit "
            "WHERE session_id_hash = ? AND action = ? AND created_at = ? "
            "LIMIT 1",
            (sid_hash, action, ts),
        ).fetchone()
        if existing is not None:
            continue
        conn.execute(
            "INSERT INTO compliance_audit "
            "(session_id_hash, action, category, actor_token_hash, "
            "payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                sid_hash, action, None, actor_hash,
                json.dumps({"demo": True, "slot": action}, sort_keys=True),
                ts,
            ),
        )
