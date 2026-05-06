"""geocode_resources_jobs — port of m010_geocode_resources_jobs.py.

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-02

Adds ``lat`` / ``lng`` columns to ``job_listings`` and creates composite
``(lat, lng)`` indexes on ``resources`` and ``job_listings``.
Backfill is handled out-of-band by ``backend/scripts/backfill_geocode_fw_data.py``.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "0010"
down_revision: Union[str, Sequence[str], None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_RES_LATLNG_INDEX = "idx_resources_latlng"
_JOB_LATLNG_INDEX = "idx_job_listings_latlng"


def upgrade() -> None:
    """Apply migration 010 — idempotent column adds + index creation."""
    bind = op.get_bind()
    _add_column_if_missing(bind, "job_listings", "lat", "REAL")
    _add_column_if_missing(bind, "job_listings", "lng", "REAL")
    op.execute(
        f"CREATE INDEX IF NOT EXISTS {_RES_LATLNG_INDEX} "
        f"ON resources(lat, lng)"
    )
    op.execute(
        f"CREATE INDEX IF NOT EXISTS {_JOB_LATLNG_INDEX} "
        f"ON job_listings(lat, lng)"
    )


def downgrade() -> None:
    """Drop the lookup indexes; leave the nullable columns in place."""
    op.execute(f"DROP INDEX IF EXISTS {_RES_LATLNG_INDEX}")
    op.execute(f"DROP INDEX IF EXISTS {_JOB_LATLNG_INDEX}")


def _has_column(bind, table: str, column: str) -> bool:
    if bind.dialect.name == "sqlite":
        rows = bind.exec_driver_sql(
            f"PRAGMA table_info({table})"
        ).fetchall()
        return any(row[1] == column for row in rows)
    row = bind.exec_driver_sql(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = %s AND column_name = %s",
        (table, column),
    ).fetchone()
    return row is not None


def _add_column_if_missing(bind, table: str, column: str, ddl: str) -> None:
    """Add a column if absent (SQLite-safe; no IF NOT EXISTS for ALTER)."""
    if not _has_column(bind, table, column):
        op.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
