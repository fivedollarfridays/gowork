"""sessions_demo_column — port of m005_sessions_demo_column.py.

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-02

Adds ``sessions.demo BOOLEAN NOT NULL DEFAULT FALSE`` for demo-data
isolation (T12.34). Idempotent on upgrade; clean round-trip on
downgrade via SQLite 3.35+ DROP COLUMN.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "0005"
down_revision: Union[str, Sequence[str], None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add sessions.demo (idempotent when already present)."""
    if _has_column(op.get_bind(), "sessions", "demo"):
        return
    op.execute(
        "ALTER TABLE sessions ADD COLUMN demo BOOLEAN NOT NULL DEFAULT FALSE"
    )


def downgrade() -> None:
    """Drop sessions.demo. No-op when the column is already absent."""
    if not _has_column(op.get_bind(), "sessions", "demo"):
        return
    op.execute("ALTER TABLE sessions DROP COLUMN demo")


def _has_column(bind, table: str, column: str) -> bool:
    """Dialect-aware column existence check."""
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
