"""Migration 005 — add `sessions.demo` flag for demo-data isolation (T12.34).

Adds a `demo BOOLEAN DEFAULT FALSE` column on `sessions` so seeded demo
rows can be excluded from analytics aggregates (T12.12 community funnel
guard already PRAGMA-checks for this column — it becomes active on
upgrade), advisor inboxes, and intelligence views.

Rationale
---------
A column is the single source of truth; `demo-` id prefixes or name
heuristics are not trustworthy. The T12.12 guard in
`funnel_queries.has_demo_column` is column-aware and transparently
no-ops when the column is absent, so no downstream refactor is needed
— applying this migration flips the guard on.

Downgrade
---------
SQLite 3.35+ supports ``ALTER TABLE ... DROP COLUMN`` directly. Python
3.12 ships sqlite3 ≥ 3.40, so no rebuild-copy dance is required for
the downgrade path. The downgrade is a clean round-trip: after it runs
the `PRAGMA table_info(sessions)` reports no `demo` column.
"""

from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 5

_COLUMN_NAME = "demo"
_ADD_COLUMN_SQL = (
    "ALTER TABLE sessions ADD COLUMN demo BOOLEAN NOT NULL DEFAULT FALSE"
)
_DROP_COLUMN_SQL = "ALTER TABLE sessions DROP COLUMN demo"


def _has_demo_column(conn: sqlite3.Connection) -> bool:
    """Return True when sessions.demo already exists (idempotency check)."""
    rows = conn.execute("PRAGMA table_info(sessions)").fetchall()
    return any(row[1] == _COLUMN_NAME for row in rows)


def upgrade(conn: sqlite3.Connection) -> None:
    """Add sessions.demo — idempotent when already present."""
    if _has_demo_column(conn):
        return
    conn.execute(_ADD_COLUMN_SQL)


def downgrade(conn: sqlite3.Connection) -> None:
    """Drop sessions.demo. No-op when the column is already absent."""
    if not _has_demo_column(conn):
        return
    conn.execute(_DROP_COLUMN_SQL)
