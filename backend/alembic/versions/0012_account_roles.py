"""account_roles — reviewer permission scaffold (T22.6).

Revision ID: 0012
Revises: 0011
Create Date: 2026-05-06

Introduces the ``account_roles`` link table:

* composite PK ``(account_id, role_name)`` — one account can hold
  any combination of roles, but each role at most once;
* ``role_name`` constrained by a SQL ``CHECK`` to the enum
  ``case_manager`` | ``sme_reviewer`` | ``dao_reviewer`` | ``admin``;
* ``granted_at`` ISO-8601 audit stamp.

DDL is delegated to :mod:`app.core.roles_schema` so the test fixture
and the alembic upgrade share one source of truth.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

from app.core.roles_schema import apply_ddl, drop_ddl

revision: str = "0012"
down_revision: Union[str, Sequence[str], None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create account_roles."""
    apply_ddl(op.get_bind())


def downgrade() -> None:
    """Drop account_roles."""
    drop_ddl(op.get_bind())
