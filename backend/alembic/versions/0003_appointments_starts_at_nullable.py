"""appointments_starts_at_nullable — port of m003.

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-02

Rebuilds the ``appointments`` table to relax ``starts_at`` to NULL.
SQLite cannot drop NOT NULL in place; the standard create-new / copy /
drop-old / rename pattern is preserved verbatim from m003 to keep the
schema byte-equivalent (the rebuilt table appears as
``CREATE TABLE "appointments"`` in sqlite_master because SQLite
preserves the source text from the rename).
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

from app.core.migrations.m003_appointments_starts_at_nullable import (
    _COPY_SQL as _M003_COPY_SQL,
)
from app.core.migrations.m003_appointments_starts_at_nullable import (
    _CREATE_NEW_TABLE as _M003_CREATE_NEW_TABLE,
)
from app.core.migrations.m003_appointments_starts_at_nullable import (
    _INDEX_DDL as _M003_INDEX_DDL,
)

from app.core.migrations.legacy_ddl_translator import (
    has_table,
    translate_for_dialect,
)

revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rebuild appointments with nullable starts_at (no-op if absent)."""
    bind = op.get_bind()
    if not has_table(bind, "appointments"):
        return
    op.execute(translate_for_dialect(_M003_CREATE_NEW_TABLE, bind.dialect.name))
    op.execute(_M003_COPY_SQL)
    op.execute("DROP TABLE appointments")
    op.execute("ALTER TABLE appointments_new RENAME TO appointments")
    for ddl in _M003_INDEX_DDL:
        op.execute(ddl)


def downgrade() -> None:
    """No-op — re-tightening NOT NULL would fail on existing rows."""
    return
