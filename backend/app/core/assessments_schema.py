"""Identity-of-content DDL for the assessment authoring layer (T23.1).

Defines the four tables introduced by alembic revision 0013:

* ``assessments`` — durable identity (slug, kind, track) per assessment.
  One row per assessment concept; never deleted, only retired.
* ``assessment_versions`` — frozen-on-publish snapshot rows; each
  publish creates a new immutable version. UNIQUE(assessment_id,
  version_number) keeps the numbering monotonic per assessment.
* ``assessment_questions`` — questions belong to a *version* (not an
  assessment), so revising a question never invalidates a past score.
  UNIQUE(version_id, position) keeps the question order stable.
* ``assessment_reviews`` — append-only review trail; one row per
  reviewer action (approve / reject / request_revision).

Schema is expressed via SQLAlchemy Core so the same definitions
generate dialect-correct DDL on both sqlite (aiosqlite) and postgres
(asyncpg). The alembic revision and the test fixture both consume
this module so the two code paths can never drift.

Enum enforcement
----------------
postgres has a native ``ENUM`` type but sqlite does not. To keep one
portable definition, every ENUM-style column is constrained with a
SQL ``CHECK`` clause that lists the valid values; both dialects
honour this and both raise ``IntegrityError`` on invalid inserts.
The module-level tuples (``ASSESSMENT_KINDS``, ``ASSESSMENT_TRACKS``,
``ASSESSMENT_VERSION_STATUSES``, ``QUESTION_KINDS``,
``REVIEW_ACTIONS``) are the single source of truth — application
code should reference those tuples rather than hard-coding strings.

Shared MetaData
---------------
This module reuses :data:`app.core.accounts_schema.metadata` so the
foreign keys to ``accounts.id`` resolve at ``create_all`` time
(matches the pattern used by ``roles_schema``). The ``apply_ddl``
helper still scopes ``create_all`` to *just* the four assessment
tables, so revision 0013 only emits DDL for what it owns.
"""

from __future__ import annotations

import sqlalchemy as sa

from app.core.accounts_schema import metadata as accounts_metadata

#: Canonical kind enum for the ``assessments.kind`` column.
ASSESSMENT_KINDS: tuple[str, ...] = (
    "skill_probe",
    "situational",
    "knowledge_check",
    "work_sample",
)

#: Canonical track enum for the ``assessments.track`` column.
ASSESSMENT_TRACKS: tuple[str, ...] = ("vocational", "dao_tech", "generic")

#: Canonical status enum for the ``assessment_versions.status`` column.
ASSESSMENT_VERSION_STATUSES: tuple[str, ...] = (
    "draft",
    "in_review",
    "approved",
    "published",
    "retired",
    "rejected",
)

#: Canonical kind enum for the ``assessment_questions.kind`` column.
QUESTION_KINDS: tuple[str, ...] = ("mcq", "freeform", "code", "scenario")

#: Canonical action enum for the ``assessment_reviews.action`` column.
REVIEW_ACTIONS: tuple[str, ...] = ("approve", "reject", "request_revision")


def _check_in_clause(column: str, values: tuple[str, ...]) -> str:
    """Render a portable ``column IN ('a','b',...)`` CHECK clause."""
    quoted = ", ".join(f"'{v}'" for v in values)
    return f"{column} IN ({quoted})"


# ---------------------------------------------------------------------------
# Tables — defined on the shared accounts metadata so FKs to
# ``accounts.id`` resolve cleanly during ``create_all``. The
# ``apply_ddl`` helper below scopes the actual emit to just these
# four tables.
# ---------------------------------------------------------------------------

assessments_table = sa.Table(
    "assessments",
    accounts_metadata,
    sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
    sa.Column("slug", sa.String(length=160), nullable=False, unique=True),
    sa.Column("kind", sa.String(length=32), nullable=False),
    sa.Column("track", sa.String(length=32), nullable=False),
    sa.Column(
        "created_by",
        sa.Integer(),
        sa.ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column("created_at", sa.String(length=64), nullable=False),
    sa.Column("retired_at", sa.String(length=64), nullable=True),
    sa.CheckConstraint(
        _check_in_clause("kind", ASSESSMENT_KINDS),
        name="ck_assessments_kind",
    ),
    sa.CheckConstraint(
        _check_in_clause("track", ASSESSMENT_TRACKS),
        name="ck_assessments_track",
    ),
)


assessment_versions_table = sa.Table(
    "assessment_versions",
    accounts_metadata,
    sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
    sa.Column(
        "assessment_id",
        sa.Integer(),
        sa.ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("version_number", sa.Integer(), nullable=False),
    sa.Column("status", sa.String(length=32), nullable=False),
    sa.Column(
        "drafted_by",
        sa.Integer(),
        sa.ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column(
        "reviewed_by",
        sa.Integer(),
        sa.ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=True,
    ),
    sa.Column(
        "approved_by",
        sa.Integer(),
        sa.ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=True,
    ),
    sa.Column("published_at", sa.String(length=64), nullable=True),
    sa.Column("retired_at", sa.String(length=64), nullable=True),
    sa.Column("created_at", sa.String(length=64), nullable=False),
    sa.UniqueConstraint(
        "assessment_id",
        "version_number",
        name="uq_assessment_versions_assessment_id_version_number",
    ),
    sa.CheckConstraint(
        _check_in_clause("status", ASSESSMENT_VERSION_STATUSES),
        name="ck_assessment_versions_status",
    ),
    # Reviewer-queue hot path: filter by track (joined to assessments)
    # and status. Keeping the index on (track, status) at the version
    # level requires the join-key column too — but the typical query
    # is "give me all versions in 'in_review' for track X", which is
    # served by an index on status alone plus a hash join on the
    # assessments side. We index (status,) directly here since track
    # lives on the parent table; that matches the spec's intent of a
    # cheap reviewer-queue scan without dragging schema into a
    # denormalised state.
    sa.Index(
        "idx_assessment_versions_status",
        "status",
    ),
)


assessment_questions_table = sa.Table(
    "assessment_questions",
    accounts_metadata,
    sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
    sa.Column(
        "version_id",
        sa.Integer(),
        sa.ForeignKey("assessment_versions.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("position", sa.Integer(), nullable=False),
    sa.Column("prompt", sa.Text(), nullable=False),
    sa.Column("kind", sa.String(length=32), nullable=False),
    sa.Column("rubric_json", sa.Text(), nullable=False),
    sa.Column(
        "scoring_weight",
        sa.Float(),
        nullable=False,
        server_default=sa.text("1.0"),
    ),
    sa.UniqueConstraint(
        "version_id",
        "position",
        name="uq_assessment_questions_version_id_position",
    ),
    sa.CheckConstraint(
        _check_in_clause("kind", QUESTION_KINDS),
        name="ck_assessment_questions_kind",
    ),
)


assessment_reviews_table = sa.Table(
    "assessment_reviews",
    accounts_metadata,
    sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
    sa.Column(
        "version_id",
        sa.Integer(),
        sa.ForeignKey("assessment_versions.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column(
        "reviewer_id",
        sa.Integer(),
        sa.ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    sa.Column("action", sa.String(length=32), nullable=False),
    sa.Column("comment", sa.Text(), nullable=True),
    sa.Column("created_at", sa.String(length=64), nullable=False),
    sa.CheckConstraint(
        _check_in_clause("action", REVIEW_ACTIONS),
        name="ck_assessment_reviews_action",
    ),
)


#: The four tables this module owns, in FK-dependency order
#: (parents before children). ``apply_ddl`` and ``drop_ddl`` use this
#: list to scope DDL to just the assessments family, leaving the
#: accounts/role tables to their own revisions.
_ASSESSMENT_TABLES = (
    assessments_table,
    assessment_versions_table,
    assessment_questions_table,
    assessment_reviews_table,
)


def apply_ddl(connection) -> None:
    """Create the four assessment tables on *connection* (idempotent).

    Scoped via ``tables=`` so this helper does not re-emit the
    accounts/role DDL that lives in revisions 0011/0012 — the three
    revisions stay surface-disjoint even though they share one
    MetaData for FK resolution. Idempotent on both engines
    (``checkfirst=True`` is the SQLAlchemy default).

    Used by:

    * ``backend/alembic/versions/0013_assessments.py`` (sync
      ``op.get_bind()`` connection during ``alembic upgrade head``).
    * ``backend/tests/test_assessments_schema.py`` (sync helper
      passed to ``AsyncConnection.run_sync`` so the DDL applies on
      top of the legacy + accounts schemas already produced by the
      ``db_engine`` fixture).
    """
    accounts_metadata.create_all(connection, tables=list(_ASSESSMENT_TABLES))


def drop_ddl(connection) -> None:
    """Drop the four assessment tables in reverse-FK order.

    Mirror of :func:`apply_ddl` for use in alembic ``downgrade``.
    SQLAlchemy's ``drop_all`` honours FK ordering automatically when
    the tables are passed explicitly.
    """
    accounts_metadata.drop_all(connection, tables=list(_ASSESSMENT_TABLES))
