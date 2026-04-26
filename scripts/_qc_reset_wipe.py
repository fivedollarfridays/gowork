"""Wipe-phase helpers for :mod:`scripts.qc_reset` (S13 T13.3).

Extracted from the CLI hub so the public script stays under the
arch-rule function-count ceiling. Pure SQL helpers — no argparse, no
config, no stdout. Each helper is a thin DELETE with a returned
rowcount.

The wipe is invoked inside a single transaction by
:func:`wipe_demo_rows`; the per-table delete helpers are exported only
for unit-test introspection.
"""

from __future__ import annotations

import hashlib
import sqlite3


__all__ = [
    "SESSION_KEYED_TABLES",
    "PLACEHOLDER_SESSION_ID",
    "wipe_demo_rows",
]


# Directly-cascading session-keyed tables. Order is auditable: each
# DELETE produces a per-table rowcount in the summary.
SESSION_KEYED_TABLES: tuple[str, ...] = (
    "appointments",
    "job_applications",
    "resume_versions",
    "daily_progress_snapshots",
    "engagement_events",
    "plan_history",
    "outcomes_records",
    "reminder_cooldowns",
    "worker_unavailability",
    "feedback_tokens",
    "visit_feedback",
    "resource_feedback",
    "record_profiles",
    "share_tokens",
)


PLACEHOLDER_SESSION_ID = "_advisor_audit"


def wipe_demo_rows(db_path: str) -> dict[str, int]:
    """Run the wipe phase as a single transaction; return per-table delete counts."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        demo_ids = _demo_session_ids(conn)
        deleted: dict[str, int] = {}
        for table in SESSION_KEYED_TABLES:
            deleted[table] = _delete_by_session_ids(conn, table, demo_ids)
        deleted["compliance_audit"] = _delete_compliance_audit(conn, demo_ids)
        deleted["advisor_tokens"] = _delete_demo_advisor_tokens(conn)
        deleted["sendgrid_events"] = _delete_demo_sendgrid_events(conn)
        deleted["sessions"] = _delete_demo_sessions(conn)
        conn.commit()
        return deleted
    finally:
        conn.close()


def _demo_session_ids(conn: sqlite3.Connection) -> list[str]:
    """Return the list of demo session ids (excluding the audit placeholder)."""
    rows = conn.execute(
        "SELECT id FROM sessions WHERE demo = 1 AND id != ?",
        (PLACEHOLDER_SESSION_ID,),
    ).fetchall()
    return [row[0] for row in rows]


def _delete_by_session_ids(
    conn: sqlite3.Connection, table: str, demo_ids: list[str],
) -> int:
    """Delete from ``table`` where ``session_id`` matches a demo id.

    Also wipes any rows tied to the ``_advisor_audit`` placeholder so
    its child rows do not accumulate across resets — the placeholder
    itself is preserved in ``sessions`` but its engagement-event
    children are fair game.
    """
    targets = list(demo_ids) + [PLACEHOLDER_SESSION_ID]
    placeholders = ",".join("?" * len(targets))
    cur = conn.execute(
        f"DELETE FROM {table} WHERE session_id IN ({placeholders})",
        targets,
    )
    return cur.rowcount or 0


def _delete_compliance_audit(
    conn: sqlite3.Connection, demo_ids: list[str],
) -> int:
    """Delete compliance_audit rows whose hashed session id is a demo session."""
    if not demo_ids:
        return 0
    hashes = [hashlib.sha256(sid.encode("utf-8")).hexdigest() for sid in demo_ids]
    placeholders = ",".join("?" * len(hashes))
    cur = conn.execute(
        f"DELETE FROM compliance_audit "
        f"WHERE session_id_hash IN ({placeholders})",
        hashes,
    )
    return cur.rowcount or 0


def _delete_demo_advisor_tokens(conn: sqlite3.Connection) -> int:
    """Delete the seeded demo advisor tokens (one per city)."""
    cur = conn.execute(
        "DELETE FROM advisor_tokens WHERE advisor_id LIKE 'adv-demo-%'"
    )
    return cur.rowcount or 0


def _delete_demo_sendgrid_events(conn: sqlite3.Connection) -> int:
    """Delete sendgrid_events with the deterministic ``demo-`` message_id prefix.

    The seed plants ``demo-sendgrid-msg-...`` rows; ops or QC harnesses
    would never use the ``demo-`` prefix on a real message_id, so the
    LIKE filter is safe.
    """
    cur = conn.execute(
        "DELETE FROM sendgrid_events WHERE message_id LIKE 'demo-%'"
    )
    return cur.rowcount or 0


def _delete_demo_sessions(conn: sqlite3.Connection) -> int:
    """Delete demo sessions, preserving the ``_advisor_audit`` placeholder."""
    cur = conn.execute(
        "DELETE FROM sessions WHERE demo = 1 AND id != ?",
        (PLACEHOLDER_SESSION_ID,),
    )
    return cur.rowcount or 0
