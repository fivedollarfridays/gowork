"""Two-sided listing verification DDL (T24.1).

Defines the four tables introduced by alembic revision 0014:

* ``employer_accounts`` — verified-claim identity (one row per
  company entity; distinct from ``accounts`` which are humans).
* ``listing_claims`` — claim attempts: SHA-256 hash of the magic-link
  token (never the raw token), the listing, the claimant's email +
  optional account, and the expiry.
* ``listing_verifications`` — one verification record per listing
  (``UNIQUE(listing_id)``); carries tier + freeform JSON intake blob.
* ``listing_reputation_events`` — append-only event stream for the
  rolling-window reputation hot path; indexed on
  ``(listing_id, occurred_at)``.

Schema is expressed via SQLAlchemy Core so the same definitions
generate dialect-correct DDL on both sqlite (aiosqlite) and postgres
(asyncpg). The alembic revision and the test fixture both consume
this module so the two code paths can never drift.

Enum enforcement: postgres has a native ``ENUM`` but sqlite does
not, so every ENUM-style column is constrained with a portable
SQL ``CHECK`` clause whose values come from the module-level
tuples (single source of truth for the app layer).

Shared MetaData: reuses :data:`app.core.accounts_schema.metadata`
(matches ``roles_schema`` / ``assessments_schema``) so FKs to
``accounts.id`` resolve cleanly during ``create_all``. ``apply_ddl``
still scopes the emit to just the four verification tables.
"""

from __future__ import annotations

import sqlalchemy as sa

from app.core.accounts_schema import metadata as accounts_metadata

#: Canonical status enum for ``employer_accounts.verification_status``.
VERIFICATION_STATUSES: tuple[str, ...] = (
    "pending",
    "claimed",
    "admin_review",
    "verified",
    "retired",
)

#: Canonical tier enum for ``employer_accounts.source_trust_tier``.
SOURCE_TRUST_TIERS: tuple[str, ...] = (
    "unknown",
    "brightdata",
    "honestjobs",
    "twc",
    "manual",
)

#: Canonical tier enum for ``listing_verifications.verification_tier``.
VERIFICATION_TIERS: tuple[str, ...] = (
    "source_trust",
    "claim_verified",
    "admin_reviewed",
)

#: Canonical kind enum for ``listing_reputation_events.event_kind``.
EVENT_KINDS: tuple[str, ...] = (
    "response_received",
    "withdrawn",
    "placed",
    "ghosted",
)


def _check_in_clause(column: str, values: tuple[str, ...]) -> str:
    """Render a portable ``column IN ('a','b',...)`` CHECK clause."""
    quoted = ", ".join(f"'{v}'" for v in values)
    return f"{column} IN ({quoted})"


# Reference-only stub for the legacy ``job_listings`` table (owned by
# raw-DDL m001, not SQLAlchemy Core). Our FK columns need a registered
# Table to resolve targets at sort time; ``apply_ddl`` below scopes the
# emit to only the four verification tables, so this stub never appears
# in emitted DDL. ``extend_existing=True`` keeps the stub idempotent if
# another module also registers ``job_listings`` on the same MetaData.
_job_listings_ref = sa.Table(
    "job_listings",
    accounts_metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    extend_existing=True,
)


# Tables — on the shared accounts MetaData so FKs to ``accounts.id``
# resolve at ``create_all``. ``apply_ddl`` scopes the emit to these
# four tables only.

employer_accounts_table = sa.Table(
    "employer_accounts",
    accounts_metadata,
    sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
    sa.Column("name", sa.String(length=255), nullable=False, unique=True),
    sa.Column("domain", sa.String(length=255), nullable=True),
    sa.Column(
        "verification_status",
        sa.String(length=32),
        nullable=False,
        server_default=sa.text("'pending'"),
    ),
    sa.Column("verified_at", sa.String(length=64), nullable=True),
    sa.Column(
        "verified_by_account_id",
        sa.Integer(),
        sa.ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
    ),
    sa.Column("retired_at", sa.String(length=64), nullable=True),
    sa.Column(
        "source_trust_tier",
        sa.String(length=32),
        nullable=False,
        server_default=sa.text("'unknown'"),
    ),
    sa.Column("created_at", sa.String(length=64), nullable=False),
    sa.CheckConstraint(
        _check_in_clause("verification_status", VERIFICATION_STATUSES),
        name="ck_employer_accounts_verification_status",
    ),
    sa.CheckConstraint(
        _check_in_clause("source_trust_tier", SOURCE_TRUST_TIERS),
        name="ck_employer_accounts_source_trust_tier",
    ),
)


listing_claims_table = sa.Table(
    "listing_claims",
    accounts_metadata,
    sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
    sa.Column(
        "claim_token_hash",
        sa.String(length=128),
        nullable=False,
        unique=True,
    ),
    sa.Column(
        "listing_id",
        sa.Integer(),
        sa.ForeignKey("job_listings.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column(
        "employer_account_id",
        sa.Integer(),
        sa.ForeignKey("employer_accounts.id", ondelete="SET NULL"),
        nullable=True,
    ),
    sa.Column("claimant_email", sa.String(length=320), nullable=False),
    sa.Column(
        "claimant_account_id",
        sa.Integer(),
        sa.ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
    ),
    sa.Column("expires_at", sa.String(length=64), nullable=False),
    sa.Column("used_at", sa.String(length=64), nullable=True),
    sa.Column("created_at", sa.String(length=64), nullable=False),
)


listing_verifications_table = sa.Table(
    "listing_verifications",
    accounts_metadata,
    sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
    sa.Column(
        "listing_id",
        sa.Integer(),
        sa.ForeignKey("job_listings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    ),
    sa.Column(
        "employer_account_id",
        sa.Integer(),
        sa.ForeignKey("employer_accounts.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column("verification_tier", sa.String(length=32), nullable=False),
    sa.Column("intake_completed_at", sa.String(length=64), nullable=True),
    sa.Column("intake_json", sa.Text(), nullable=True),
    sa.Column("verified_at", sa.String(length=64), nullable=False),
    sa.Column("created_at", sa.String(length=64), nullable=False),
    sa.CheckConstraint(
        _check_in_clause("verification_tier", VERIFICATION_TIERS),
        name="ck_listing_verifications_verification_tier",
    ),
)


listing_reputation_events_table = sa.Table(
    "listing_reputation_events",
    accounts_metadata,
    sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
    sa.Column(
        "listing_id",
        sa.Integer(),
        sa.ForeignKey("job_listings.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("event_kind", sa.String(length=32), nullable=False),
    sa.Column("session_id", sa.String(length=64), nullable=True),
    sa.Column("occurred_at", sa.String(length=64), nullable=False),
    sa.Column(
        "recorded_by",
        sa.Integer(),
        sa.ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
    ),
    sa.Column("notes", sa.Text(), nullable=True),
    sa.CheckConstraint(
        _check_in_clause("event_kind", EVENT_KINDS),
        name="ck_listing_reputation_events_event_kind",
    ),
    # Rolling-window reputation hot path: filter by listing + order
    # by occurred_at. sqlite ignores asc/desc on b-tree leaves, so
    # column-order serves the same scan plan on both engines.
    sa.Index(
        "idx_listing_reputation_events_listing_id_occurred_at",
        "listing_id",
        "occurred_at",
    ),
)


#: Tables owned here, in FK-dependency order (parents before
#: children). ``apply_ddl`` / ``drop_ddl`` scope DDL to this set so
#: the verification family stays surface-disjoint from the accounts/
#: role/assessment revisions even though they share one MetaData.
_VERIFICATION_TABLES = (
    employer_accounts_table,
    listing_claims_table,
    listing_verifications_table,
    listing_reputation_events_table,
)


def apply_ddl(connection) -> None:
    """Create the four verification tables on *connection* (idempotent).

    Used by ``backend/alembic/versions/0014_listing_verification.py``
    (sync ``op.get_bind()`` during ``alembic upgrade head``) and by
    ``backend/tests/test_listings_verification_schema.py`` (sync
    helper passed to ``AsyncConnection.run_sync`` so the DDL applies
    on top of the legacy + accounts schemas produced by ``db_engine``).
    """
    accounts_metadata.create_all(
        connection, tables=list(_VERIFICATION_TABLES)
    )


def drop_ddl(connection) -> None:
    """Drop the four verification tables in reverse-FK order.

    Mirror of :func:`apply_ddl` for use in alembic ``downgrade``;
    SQLAlchemy's ``drop_all`` honours FK ordering automatically.
    """
    accounts_metadata.drop_all(
        connection, tables=list(_VERIFICATION_TABLES)
    )
