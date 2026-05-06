"""used_tokens — port of m004_used_tokens.py.

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-02

Single-use manage-appointment token replay protection (T12.10b).
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

from app.core.migrations.m004_used_tokens import DDL_SQL as _M004_DDL_SQL
from app.core.migrations.m004_used_tokens import _INDEX_DDL as _M004_INDEX_DDL

revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create used_tokens table + audit index."""
    op.execute(_M004_DDL_SQL)
    for ddl in _M004_INDEX_DDL:
        op.execute(ddl)


def downgrade() -> None:
    """Drop used_tokens table (clears all replay history)."""
    op.execute("DROP TABLE IF EXISTS used_tokens")
