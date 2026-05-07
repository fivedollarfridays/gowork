"""accounts — identity layer foundation (T22.5).

Revision ID: 0011
Revises: 0010
Create Date: 2026-05-06

Introduces three tables:

* ``accounts`` — durable identity (one row per email).
* ``account_sessions`` — link table binding ``accounts.id`` to one or
  more anonymous ``sessions.id`` values; ``UNIQUE(session_id)`` keeps
  a session pinned to at most one account.
* ``account_credentials`` — magic-link tokens today, generic enough
  to host oauth/phone credentials in later sprints.

DDL is delegated to :mod:`app.core.accounts_schema` so the test
fixture and the alembic upgrade share one source of truth.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

from app.core.accounts_schema import apply_ddl, drop_ddl

revision: str = "0011"
down_revision: Union[str, Sequence[str], None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create accounts, account_sessions, account_credentials."""
    apply_ddl(op.get_bind())


def downgrade() -> None:
    """Drop the identity tables in reverse-dependency order."""
    drop_ddl(op.get_bind())
