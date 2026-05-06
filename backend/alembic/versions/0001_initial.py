"""initial — port of m001_initial.py.

Revision ID: 0001
Revises:
Create Date: 2026-05-02

DDL is re-exported from ``app.core.migrations.m001_initial`` to guarantee
byte-equivalence with the legacy runner. The downgrade order mirrors
``m001_initial._DOWNGRADE_ORDER`` (children before parents).
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

from app.core.migrations.m001_initial import DDL_SQL as _M001_DDL_SQL
from app.core.migrations.m001_initial import _DOWNGRADE_ORDER as _M001_DROP_ORDER

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration 001 — initial schema (16 tables)."""
    bind = op.get_bind()
    # m001's DDL is a single ``executescript``-style blob; replay it
    # statement-by-statement so it works on every dialect (sqlite +
    # postgres). Empty fragments from the trailing semicolons are
    # filtered out.
    for stmt in _split_sql(_M001_DDL_SQL):
        bind.exec_driver_sql(stmt)


def downgrade() -> None:
    """Drop tables created by m001 in reverse-dependency order."""
    for table in _M001_DROP_ORDER:
        op.execute(f"DROP TABLE IF EXISTS {table}")


def _split_sql(blob: str) -> list[str]:
    """Split a multi-statement DDL blob into individual statements."""
    return [s.strip() for s in blob.split(";") if s.strip()]
