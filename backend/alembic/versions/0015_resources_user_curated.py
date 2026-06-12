"""resources_user_curated — admin-curation timestamp on resources (T26.1).

Revision ID: 0015
Revises: 0014
Create Date: 2026-05-09

Adds ``resources.user_curated_at TIMESTAMP NULL`` so the seed loader
can distinguish admin-curated rows from auto-seeded rows. Default
NULL preserves the legacy single-city behaviour: every existing row
is "uncurated" and the seed loader treats it normally. T26.2's CRUD
writes will stamp this column to ``now()`` on every admin INSERT and
UPDATE, completing the contract that prevents container-restart
seeding from clobbering manual edits.

Downgrade is a no-op: SQLite < 3.35 cannot DROP COLUMN, and on
postgres dropping the column would erase the curation history this
migration was designed to retain.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

from app.core.migrations.legacy_ddl_translator import has_column

revision: str = "0015"
down_revision: Union[str, Sequence[str], None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add resources.user_curated_at (idempotent)."""
    if not has_column(op.get_bind(), "resources", "user_curated_at"):
        op.execute(
            "ALTER TABLE resources ADD COLUMN user_curated_at TIMESTAMP"
        )


def downgrade() -> None:
    """No-op: SQLite < 3.35 can't drop columns; postgres path keeps history."""
    return
