"""Migration 010 — geocoding columns on ``job_listings`` + lookup index.

Resources already have ``lat`` / ``lng`` columns from m001. Jobs do not.
This migration:

1. Adds ``lat REAL`` and ``lng REAL`` to ``job_listings`` (NULL-safe).
2. Adds a composite index on ``(lat, lng)`` for both ``resources`` and
   ``job_listings`` so distance-based filtering in the matcher does not
   table-scan once we have meaningful geocoded data.

Backfilling the actual coordinates is handled out-of-band by
``backend/scripts/backfill_geocode_fw_data.py`` — running the geocoder
synchronously inside the migration would block ASGI startup for ~3
minutes and is the wrong place for it.

Idempotency
-----------
``ALTER TABLE`` is wrapped in a defensive PRAGMA check; ``CREATE INDEX
IF NOT EXISTS`` is naturally idempotent.

Downgrade
---------
SQLite < 3.35 cannot DROP COLUMN; we drop the indexes only and leave
the columns in place (they are nullable, so legacy code paths that
don't know about them are unaffected).
"""

from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 10

_RES_LATLNG_INDEX = "idx_resources_latlng"
_JOB_LATLNG_INDEX = "idx_job_listings_latlng"


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Return True iff *table* already has *column*."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def _add_column_if_missing(
    conn: sqlite3.Connection, table: str, column: str, ddl: str,
) -> None:
    """Add a column if absent (SQLite-safe; no IF NOT EXISTS for ALTER)."""
    if not _column_exists(conn, table, column):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def upgrade(conn: sqlite3.Connection) -> None:
    """Apply migration 010 — idempotent column adds + index creation."""
    _add_column_if_missing(conn, "job_listings", "lat", "REAL")
    _add_column_if_missing(conn, "job_listings", "lng", "REAL")
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS {_RES_LATLNG_INDEX} "
        f"ON resources(lat, lng)",
    )
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS {_JOB_LATLNG_INDEX} "
        f"ON job_listings(lat, lng)",
    )


def downgrade(conn: sqlite3.Connection) -> None:
    """Drop the lookup indexes; leave the nullable columns in place."""
    conn.execute(f"DROP INDEX IF EXISTS {_RES_LATLNG_INDEX}")
    conn.execute(f"DROP INDEX IF EXISTS {_JOB_LATLNG_INDEX}")
