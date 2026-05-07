"""s12_worker_companion — port of m002_s12_worker_companion.py.

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-02

Re-exports the table + index DDL tuples from
``app.core.migrations.m002_s12_worker_companion`` so the migration text
remains the single source of truth (byte-equivalence guarantee).
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

from app.core.migrations.m002_s12_worker_companion import (
    _DOWNGRADE_ORDER as _M002_DROP_ORDER,
)
from app.core.migrations.m002_s12_worker_companion import (
    _INDEX_DDL as _M002_INDEX_DDL,
)
from app.core.migrations.m002_s12_worker_companion import (
    _TABLE_DDL as _M002_TABLE_DDL,
)

from app.core.migrations.legacy_ddl_translator import translate_for_dialect

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create S12 worker-companion tables + indexes (13 tables)."""
    dialect = op.get_bind().dialect.name
    for ddl in _M002_TABLE_DDL:
        op.execute(translate_for_dialect(ddl, dialect))
    for ddl in _M002_INDEX_DDL:
        op.execute(ddl)


def downgrade() -> None:
    """Drop S12 worker-companion tables (indexes drop with their tables)."""
    for table in _M002_DROP_ORDER:
        op.execute(f"DROP TABLE IF EXISTS {table}")
