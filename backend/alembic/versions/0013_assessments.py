"""assessments — identity-of-content layer for authoring (T23.1).

Revision ID: 0013
Revises: 0012
Create Date: 2026-05-07

Introduces four tables:

* ``assessments`` — durable identity (slug, kind, track) per assessment.
* ``assessment_versions`` — frozen-on-publish snapshot rows; UNIQUE on
  ``(assessment_id, version_number)``.
* ``assessment_questions`` — questions attached to a *version*, so a
  revision never invalidates a past score; UNIQUE on
  ``(version_id, position)``.
* ``assessment_reviews`` — append-only reviewer audit trail.

DDL is delegated to :mod:`app.core.assessments_schema` so the test
fixture and the alembic upgrade share one source of truth.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

from app.core.assessments_schema import apply_ddl, drop_ddl

revision: str = "0013"
down_revision: Union[str, Sequence[str], None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the four assessment tables in FK-dependency order."""
    apply_ddl(op.get_bind())


def downgrade() -> None:
    """Drop the four assessment tables in reverse-FK order."""
    drop_ddl(op.get_bind())
