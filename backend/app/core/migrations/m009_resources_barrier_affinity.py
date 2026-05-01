"""Migration 009 — store explicit ``barrier_affinity`` on resources.

Adds a JSON-encoded ``barrier_affinity`` column to the ``resources``
table so the Stage-2 affinity router can route a resource to one or
more barrier cards without relying on name-keyword heuristics.

Schema notes
------------
* Column type: TEXT, JSON-encoded list (``["transportation",
  "criminal_record"]``). NULL is permitted for legacy un-tagged rows.
* No index — barrier_affinity is read in-process per resource, never
  filtered at the SQL layer.

Idempotency
-----------
The ``ALTER TABLE`` is wrapped in a defensive PRAGMA check — re-running
the migration on a DB that already has the column is a no-op.

Downgrade
---------
SQLite < 3.35 cannot DROP COLUMN.  Downgrade is a best-effort no-op:
the column stays, future inserts simply leave it NULL.
"""

from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 9


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Return True iff *table* has *column*."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def upgrade(conn: sqlite3.Connection) -> None:
    """Add ``resources.barrier_affinity`` (idempotent)."""
    if not _column_exists(conn, "resources", "barrier_affinity"):
        conn.execute(
            "ALTER TABLE resources ADD COLUMN barrier_affinity TEXT",
        )


def downgrade(conn: sqlite3.Connection) -> None:
    """No-op: SQLite < 3.35 can't drop columns; we leave it in place."""
    return
