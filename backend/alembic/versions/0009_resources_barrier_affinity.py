"""resources_barrier_affinity — port of m009_resources_barrier_affinity.py.

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-02

Adds ``resources.barrier_affinity`` (TEXT, JSON-encoded list) so the
Stage-2 affinity router can route resources without keyword heuristics.
No supporting index — column is read in-process per resource.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

from app.core.migrations.legacy_ddl_translator import has_column

revision: str = "0009"
down_revision: Union[str, Sequence[str], None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add resources.barrier_affinity (idempotent)."""
    if not has_column(op.get_bind(), "resources", "barrier_affinity"):
        op.execute(
            "ALTER TABLE resources ADD COLUMN barrier_affinity TEXT"
        )


def downgrade() -> None:
    """No-op: SQLite < 3.35 can't drop columns."""
    return
