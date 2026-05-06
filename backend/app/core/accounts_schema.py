"""Identity-layer DDL for the ``accounts`` family of tables (T22.5).

Defines the three tables introduced by alembic revision 0011:

* ``accounts`` — durable identity (one row per real human/email).
* ``account_sessions`` — link rows binding an account to one or more
  anonymous ``sessions.id`` values.  ``UNIQUE(session_id)`` enforces
  the invariant that a session belongs to at most one account.
* ``account_credentials`` — generic credential store (magic-link
  tokens today; oauth/phone tomorrow).  ``credential_value_hash``
  is the SHA-256 of the token; we never persist the raw token.

Schema is expressed via SQLAlchemy Core so the same definitions
generate dialect-correct DDL on both sqlite (aiosqlite) and postgres
(asyncpg). The alembic revision and the test fixture both consume
this module so the two code paths can never drift.
"""

from __future__ import annotations

import sqlalchemy as sa

#: SQLAlchemy MetaData container for the identity layer.  Kept private
#: (no foreign-key reflection of legacy tables) so callers can't accidentally
#: ``create_all`` the entire app schema through this object.
metadata = sa.MetaData()


accounts_table = sa.Table(
    "accounts",
    metadata,
    sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
    sa.Column("email", sa.String(length=320), nullable=False, unique=True),
    sa.Column("created_at", sa.String(length=64), nullable=False),
    sa.Column("last_active_at", sa.String(length=64), nullable=True),
)


account_sessions_table = sa.Table(
    "account_sessions",
    metadata,
    sa.Column(
        "account_id",
        sa.Integer(),
        sa.ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("session_id", sa.String(length=64), nullable=False, unique=True),
    sa.Column("claimed_at", sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint("account_id", "session_id"),
)


account_credentials_table = sa.Table(
    "account_credentials",
    metadata,
    sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
    sa.Column(
        "account_id",
        sa.Integer(),
        sa.ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("credential_type", sa.String(length=32), nullable=False),
    sa.Column("credential_value_hash", sa.String(length=128), nullable=False),
    sa.Column("expires_at", sa.String(length=64), nullable=False),
    sa.Column("used_at", sa.String(length=64), nullable=True),
    sa.Index(
        "idx_account_credentials_lookup",
        "credential_type",
        "credential_value_hash",
    ),
)


def apply_ddl(connection) -> None:
    """Create the identity tables on *connection* (idempotent).

    Used by:

    * ``backend/alembic/versions/0011_accounts.py`` (sync ``op.get_bind()``
      connection during ``alembic upgrade head``).
    * ``backend/tests/test_accounts.py`` (sync helper passed to
      ``AsyncConnection.run_sync`` so the same DDL applies on top of the
      legacy m001..m010 schema produced by ``init_db``).
    """
    metadata.create_all(connection)


def drop_ddl(connection) -> None:
    """Drop the identity tables on *connection* (idempotent).

    Mirror of :func:`apply_ddl` for use in alembic ``downgrade``.
    """
    metadata.drop_all(connection)
