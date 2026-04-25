"""Shared helpers for the T13.2 QC demo-seed tests.

Lifted out of ``test_demo_seed_s12b.py`` so the parent test file stays
under the project's 600-line test ceiling. Pure helpers — no pytest
fixtures live here so both the original file and the QC-extension
test file can share them without import side-effects.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.core.migrations import m001_initial, m002_s12_worker_companion
from app.core.migrations import m005_sessions_demo_column as m005
from app.core.migrations import m006_compliance_tombstones as m006
from app.core.migrations import m007_advisor_tokens as m007


__all__ = [
    "fresh_db",
    "apply_m005",
    "apply_through_m007",
    "qc_seed_snapshot",
]


def fresh_db(tmp_path: Path, name: str = "s12b.db") -> str:
    """Create a DB with m001 + m002 applied — baseline before m005."""
    db_path = str(tmp_path / name)
    conn = sqlite3.connect(db_path)
    try:
        m001_initial.upgrade(conn)
        m002_s12_worker_companion.upgrade(conn)
        conn.commit()
    finally:
        conn.close()
    return db_path


def apply_m005(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        m005.upgrade(conn)
        conn.commit()
    finally:
        conn.close()


def apply_through_m007(db_path: str) -> None:
    """Apply m006 + m007 on top of an m005-applied DB."""
    conn = sqlite3.connect(db_path)
    try:
        m006.upgrade(conn)
        m007.upgrade(conn)
        conn.commit()
    finally:
        conn.close()


def qc_seed_snapshot(db_path: str) -> dict[str, list]:
    """Return a deterministic snapshot of every QC seed table.

    Each row is sorted into a stable tuple so two-run comparisons are
    independent of insertion order.
    """
    conn = sqlite3.connect(db_path)
    try:
        return {
            "feedback_tokens": _select(
                conn,
                "SELECT token, session_id, expires_at FROM feedback_tokens",
            ),
            "compliance_audit": _select(
                conn,
                "SELECT session_id_hash, action, payload_json, created_at "
                "FROM compliance_audit",
            ),
            "advisor_tokens": _select(
                conn,
                "SELECT token_hash, advisor_id, city FROM advisor_tokens",
            ),
            "engagement_events": _select(
                conn,
                "SELECT session_id, category, payload_json, created_at "
                "FROM engagement_events",
            ),
            "reminder_cooldowns": _select(
                conn,
                "SELECT session_id, category, stall_level FROM reminder_cooldowns",
            ),
            "sendgrid_events": _select(
                conn,
                "SELECT event_type, email, message_id FROM sendgrid_events",
            ),
            "sessions": _select(
                conn,
                "SELECT id, demo, profile FROM sessions",
            ),
        }
    finally:
        conn.close()


def _select(conn: sqlite3.Connection, query: str) -> list:
    return sorted(conn.execute(query).fetchall())
