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

from app.core.migrations.legacy_ddl_translator import split_and_translate

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration 001 — initial schema (16 tables)."""
    bind = op.get_bind()
    # Replay the legacy DDL blob statement-by-statement; translator
    # rewrites sqlite-isms (e.g. AUTOINCREMENT) for postgres.
    for stmt in split_and_translate(_M001_DDL_SQL, bind.dialect.name):
        bind.exec_driver_sql(stmt)


def downgrade() -> None:
    """Drop tables created by m001 in reverse-dependency order."""
    for table in _M001_DROP_ORDER:
        op.execute(f"DROP TABLE IF EXISTS {table}")
