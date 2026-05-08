"""listing_verification — two-sided listing verification substrate (T24.1).

Revision ID: 0014
Revises: 0013
Create Date: 2026-05-08

Introduces four tables:

* ``employer_accounts`` — verified-claim identity (one row per
  company entity).
* ``listing_claims`` — claim attempts (token hash + listing +
  claimant + expiry).
* ``listing_verifications`` — one verification record per listing
  (``UNIQUE(listing_id)``).
* ``listing_reputation_events`` — append-only event stream for the
  rolling-window reputation hot path; indexed on
  ``(listing_id, occurred_at)``.

DDL is delegated to :mod:`app.core.listings_verification_schema` so
the test fixture and the alembic upgrade share one source of truth.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

from app.core.listings_verification_schema import apply_ddl, drop_ddl

revision: str = "0014"
down_revision: Union[str, Sequence[str], None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the four verification tables in FK-dependency order."""
    apply_ddl(op.get_bind())


def downgrade() -> None:
    """Drop the four verification tables in reverse-FK order."""
    drop_ddl(op.get_bind())
