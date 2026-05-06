"""advisor_tokens — port of m007_advisor_tokens.py.

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-02

Creates the ``advisor_tokens`` table that backs case-manager advisor
inbox auth (T12.31).
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

from app.core.migrations.m007_advisor_tokens import _INDEXES as _M007_INDEXES
from app.core.migrations.m007_advisor_tokens import _TABLE_DDL as _M007_TABLE_DDL

revision: str = "0007"
down_revision: Union[str, Sequence[str], None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create advisor_tokens + supporting indexes (idempotent)."""
    op.execute(_M007_TABLE_DDL)
    for ddl in _M007_INDEXES:
        op.execute(ddl)


def downgrade() -> None:
    """Drop advisor_tokens + its indexes. Clean round-trip."""
    op.execute("DROP INDEX IF EXISTS idx_advisor_tokens_active")
    op.execute("DROP INDEX IF EXISTS idx_advisor_tokens_advisor_id")
    op.execute("DROP TABLE IF EXISTS advisor_tokens")
