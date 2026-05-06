"""resources_city — port of m008_resources_city.py.

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-02

Adds ``resources.city`` (TEXT) and a supporting index for per-request
city filtering. Downgrade drops the index only — SQLite < 3.35 cannot
DROP COLUMN.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "0008"
down_revision: Union[str, Sequence[str], None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add resources.city (idempotent) + supporting index."""
    if not _has_column(op.get_bind(), "resources", "city"):
        op.execute("ALTER TABLE resources ADD COLUMN city TEXT")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_resources_city ON resources(city)"
    )


def downgrade() -> None:
    """Drop the index. Column stays — SQLite < 3.35 can't DROP COLUMN."""
    op.execute("DROP INDEX IF EXISTS idx_resources_city")


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
