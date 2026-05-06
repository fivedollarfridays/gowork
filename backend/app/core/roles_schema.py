"""Role-layer DDL for the ``account_roles`` table (T22.6).

Defines the single table introduced by alembic revision 0012:

* ``account_roles`` — composite-PK link table binding an account to
  zero or more roles drawn from a fixed enum (``case_manager``,
  ``sme_reviewer``, ``dao_reviewer``, ``admin``).

Schema is expressed via SQLAlchemy Core so the same DDL generates
dialect-correct statements on both sqlite (aiosqlite) and postgres
(asyncpg). The alembic revision and the test fixture both consume
this module so the two code paths can never drift.

Enum enforcement
----------------
postgres has a native ``ENUM`` type but sqlite does not. To keep one
portable definition we constrain ``role_name`` with a SQL ``CHECK``
constraint that lists the valid values; both dialects honour this and
both raise ``IntegrityError`` on invalid inserts. ``ROLE_NAMES`` below
is the single source of truth for the application layer; importers
should reference that tuple rather than hard-coding the strings.
"""

from __future__ import annotations

import sqlalchemy as sa

from app.core.accounts_schema import metadata as accounts_metadata

#: Canonical role enum. Order is presentation order (least to most
#: privileged); the SQL ``CHECK`` constraint and the application-side
#: validators both reference this tuple.
ROLE_NAMES: tuple[str, ...] = (
    "case_manager",
    "sme_reviewer",
    "dao_reviewer",
    "admin",
)


def _role_check_clause() -> str:
    """Render the ``role_name IN ('a','b',...)`` CHECK clause."""
    quoted = ", ".join(f"'{r}'" for r in ROLE_NAMES)
    return f"role_name IN ({quoted})"


#: ``account_roles`` lives in the *same* MetaData as the accounts
#: family so the FK to ``accounts.id`` resolves cleanly during
#: ``create_all``. The DDL surface here still scopes ``create_all``
#: to *just* this table via the explicit ``tables=`` arg below, so
#: revision 0012 only emits DDL for what it owns.
account_roles_table = sa.Table(
    "account_roles",
    accounts_metadata,
    sa.Column(
        "account_id",
        sa.Integer(),
        sa.ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("role_name", sa.String(length=32), nullable=False),
    sa.Column("granted_at", sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint("account_id", "role_name"),
    sa.CheckConstraint(_role_check_clause(), name="ck_account_roles_role_name"),
)


def apply_ddl(connection) -> None:
    """Create *only* the ``account_roles`` table on *connection*.

    Scoped via ``tables=[account_roles_table]`` so this helper does
    not re-emit the accounts/account_sessions/account_credentials
    DDL that already lives in revision 0011 — the two revisions stay
    surface-disjoint even though they share one MetaData for FK
    resolution. Idempotent on both engines (``checkfirst=True`` is
    the SQLAlchemy default).

    Used by:

    * ``backend/alembic/versions/0012_account_roles.py``
    * ``backend/tests/test_roles.py``
    """
    accounts_metadata.create_all(connection, tables=[account_roles_table])


def drop_ddl(connection) -> None:
    """Drop *only* ``account_roles`` (mirrors :func:`apply_ddl`)."""
    accounts_metadata.drop_all(connection, tables=[account_roles_table])
