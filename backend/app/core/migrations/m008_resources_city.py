"""Migration 008 — tag resources with their source city slug.

Adds a ``city`` column to the ``resources`` table so the matching
pipeline can filter resources by the per-request city context (set
from the user's ZIP code).  Without this, every assessment sees the
union of every city's resources, leaking Alabama resources into Fort
Worth responses (and vice versa).

Schema notes
------------
* ``city`` is the slug from ``cities/*.yaml`` (e.g. ``montgomery``,
  ``fort-worth``).  NULL is permitted for legacy rows; the seeder
  back-fills the column for any resource it loads.
* An index on ``city`` keeps the per-request query fast even at
  scale (every assessment runs ``WHERE category IN (...) AND
  city = :city``).

Idempotency
-----------
The ``ALTER TABLE`` is wrapped in a defensive PRAGMA check — re-running
the migration on a DB that already has the column is a no-op.

Downgrade
---------
SQLite versions < 3.35 cannot DROP COLUMN.  The downgrade is
best-effort: it removes the index but leaves the column.  Tests
covering the round-trip should not assume the column is gone after
``rollback``.
"""

from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 8

_INDEX_DDL = (
    "CREATE INDEX IF NOT EXISTS idx_resources_city "
    "ON resources(city)"
)


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Return True iff *table* has *column*."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def upgrade(conn: sqlite3.Connection) -> None:
    """Add ``resources.city`` (idempotent) + supporting index."""
    if not _column_exists(conn, "resources", "city"):
        conn.execute("ALTER TABLE resources ADD COLUMN city TEXT")
    conn.execute(_INDEX_DDL)


def downgrade(conn: sqlite3.Connection) -> None:
    """Drop the index. Column stays — SQLite < 3.35 can't DROP COLUMN."""
    conn.execute("DROP INDEX IF EXISTS idx_resources_city")
