"""compliance_tombstones — port of m006_compliance_tombstones.py.

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-02

Creates ``compliance_audit`` and adds tombstone columns
(``deleted_at``, ``deleted_reason``) on three sensitive tables that carry
category-partitioned PII (record_profiles, resume_versions,
engagement_events).
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

from app.core.migrations.m006_compliance_tombstones import (
    _AUDIT_INDEXES as _M006_AUDIT_INDEXES,
)
from app.core.migrations.m006_compliance_tombstones import (
    _AUDIT_TABLE_DDL as _M006_AUDIT_TABLE_DDL,
)
from app.core.migrations.m006_compliance_tombstones import (
    _TOMBSTONE_TABLES as _M006_TOMBSTONE_TABLES,
)

from app.core.migrations.legacy_ddl_translator import (
    has_column,
    translate_for_dialect,
)

revision: str = "0006"
down_revision: Union[str, Sequence[str], None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create compliance_audit + add tombstone columns (idempotent)."""
    bind = op.get_bind()
    op.execute(translate_for_dialect(_M006_AUDIT_TABLE_DDL, bind.dialect.name))
    for idx in _M006_AUDIT_INDEXES:
        op.execute(idx)
    for table in _M006_TOMBSTONE_TABLES:
        _add_tombstones(bind, table)


def downgrade() -> None:
    """Drop compliance_audit + tombstone columns. Clean round-trip."""
    bind = op.get_bind()
    for table in _M006_TOMBSTONE_TABLES:
        _drop_tombstones(bind, table)
    op.execute("DROP TABLE IF EXISTS compliance_audit")


def _add_tombstones(bind, table: str) -> None:
    """Add deleted_at + deleted_reason to ``table`` (idempotent)."""
    if not has_column(bind, table, "deleted_at"):
        op.execute(f"ALTER TABLE {table} ADD COLUMN deleted_at TEXT")
    if not has_column(bind, table, "deleted_reason"):
        op.execute(f"ALTER TABLE {table} ADD COLUMN deleted_reason TEXT")


def _drop_tombstones(bind, table: str) -> None:
    """Drop deleted_at + deleted_reason from ``table`` (no-op if absent)."""
    if has_column(bind, table, "deleted_reason"):
        op.execute(f"ALTER TABLE {table} DROP COLUMN deleted_reason")
    if has_column(bind, table, "deleted_at"):
        op.execute(f"ALTER TABLE {table} DROP COLUMN deleted_at")
