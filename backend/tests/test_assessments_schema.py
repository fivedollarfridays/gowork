"""Schema-sanity tests for the assessment authoring layer (T23.1).

Exercises the four tables introduced by alembic revision 0013:

* ``assessments`` — durable identity (slug, kind, track).
* ``assessment_versions`` — frozen-on-publish snapshot rows.
* ``assessment_questions`` — question rows belonging to a version.
* ``assessment_reviews`` — reviewer audit trail.

Schema is layered on top of the legacy ``db_engine`` schema in the
same way :mod:`backend.tests.test_roles` layers role DDL — apply
the accounts identity DDL first (FKs to ``accounts.id``) then the
assessments DDL via :func:`app.core.assessments_schema.apply_ddl`.
The tests focus on:

* presence of the four tables and their core columns,
* CHECK-constraint enforcement for every ENUM-style column,
* the (assessment_id, version_number) and (version_id, position)
  uniqueness invariants,
* the ENUM-tuple constants (single source of truth for the app
  layer) match the strings actually accepted by the CHECK clause.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import queries_accounts
from app.core.accounts_schema import apply_ddl as apply_accounts_ddl
from app.core.assessments_schema import (
    ASSESSMENT_KINDS,
    ASSESSMENT_TRACKS,
    ASSESSMENT_VERSION_STATUSES,
    QUESTION_KINDS,
    REVIEW_ACTIONS,
    apply_ddl as apply_assessments_ddl,
)


@pytest.fixture
async def assessments_engine(db_engine):
    """``db_engine`` plus accounts + assessments DDL applied on top."""
    async with db_engine.begin() as conn:
        await conn.run_sync(apply_accounts_ddl)
        await conn.run_sync(apply_assessments_ddl)
    return db_engine


@pytest.fixture
def session_factory(assessments_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        assessments_engine, class_=AsyncSession, expire_on_commit=False
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_account(session: AsyncSession, email: str) -> int:
    """Create an account row and return its id."""
    return await queries_accounts.create_account(session, email=email)


async def _insert_assessment(
    session: AsyncSession,
    *,
    slug: str,
    kind: str = "skill_probe",
    track: str = "vocational",
    created_by: int,
) -> int:
    """Insert an assessment row and return its id."""
    # ``RETURNING id`` works on sqlite (≥3.35) AND postgres (asyncpg);
    # ``result.lastrowid`` is sqlite-only and breaks on the postgres axis.
    result = await session.execute(
        text(
            "INSERT INTO assessments "
            "(slug, kind, track, created_by, created_at) "
            "VALUES (:slug, :kind, :track, :created_by, :created_at) "
            "RETURNING id"
        ),
        {
            "slug": slug,
            "kind": kind,
            "track": track,
            "created_by": created_by,
            "created_at": "2026-05-07T00:00:00Z",
        },
    )
    return int(result.scalar_one())


async def _insert_version(
    session: AsyncSession,
    *,
    assessment_id: int,
    version_number: int = 1,
    status: str = "draft",
    drafted_by: int,
) -> int:
    """Insert an assessment_versions row and return its id."""
    # ``RETURNING id`` for portable asyncpg + aiosqlite.
    result = await session.execute(
        text(
            "INSERT INTO assessment_versions "
            "(assessment_id, version_number, status, drafted_by, created_at) "
            "VALUES (:aid, :vn, :status, :drafted_by, :created_at) "
            "RETURNING id"
        ),
        {
            "aid": assessment_id,
            "vn": version_number,
            "status": status,
            "drafted_by": drafted_by,
            "created_at": "2026-05-07T00:00:00Z",
        },
    )
    return int(result.scalar_one())


# ---------------------------------------------------------------------------
# Table presence
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_assessments_table_exists(session_factory):
    """Empty SELECT proves the assessments table is present."""
    async with session_factory() as session:
        result = await session.execute(
            text(
                "SELECT id, slug, kind, track, created_by, "
                "created_at, retired_at FROM assessments"
            )
        )
        assert result.first() is None


@pytest.mark.anyio
async def test_assessment_versions_table_exists(session_factory):
    """Empty SELECT proves the assessment_versions table is present."""
    async with session_factory() as session:
        result = await session.execute(
            text(
                "SELECT id, assessment_id, version_number, status, "
                "drafted_by, reviewed_by, approved_by, published_at, "
                "retired_at, created_at FROM assessment_versions"
            )
        )
        assert result.first() is None


@pytest.mark.anyio
async def test_assessment_questions_table_exists(session_factory):
    """Empty SELECT proves the assessment_questions table is present."""
    async with session_factory() as session:
        result = await session.execute(
            text(
                "SELECT id, version_id, position, prompt, kind, "
                "rubric_json, scoring_weight FROM assessment_questions"
            )
        )
        assert result.first() is None


@pytest.mark.anyio
async def test_assessment_reviews_table_exists(session_factory):
    """Empty SELECT proves the assessment_reviews table is present."""
    async with session_factory() as session:
        result = await session.execute(
            text(
                "SELECT id, version_id, reviewer_id, action, comment, "
                "created_at FROM assessment_reviews"
            )
        )
        assert result.first() is None


# ---------------------------------------------------------------------------
# ENUM CHECK constraints
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_assessments_kind_check_rejects_invalid(session_factory):
    """assessments.kind CHECK rejects values outside the enum tuple."""
    async with session_factory() as session:
        account_id = await _make_account(session, "k@example.com")
        with pytest.raises(Exception):
            await _insert_assessment(
                session,
                slug="bad-kind",
                kind="not_a_kind",
                track="vocational",
                created_by=account_id,
            )


@pytest.mark.anyio
async def test_assessments_track_check_rejects_invalid(session_factory):
    """assessments.track CHECK rejects values outside the enum tuple."""
    async with session_factory() as session:
        account_id = await _make_account(session, "t@example.com")
        with pytest.raises(Exception):
            await _insert_assessment(
                session,
                slug="bad-track",
                kind="skill_probe",
                track="space_force",
                created_by=account_id,
            )


@pytest.mark.anyio
async def test_assessments_kind_check_accepts_all_enum_values(session_factory):
    """Every value in ASSESSMENT_KINDS is accepted by the CHECK constraint."""
    async with session_factory() as session:
        account_id = await _make_account(session, "kall@example.com")
        for i, kind in enumerate(ASSESSMENT_KINDS):
            await _insert_assessment(
                session,
                slug=f"k-{i}",
                kind=kind,
                track="vocational",
                created_by=account_id,
            )


@pytest.mark.anyio
async def test_assessment_versions_status_check_rejects_invalid(
    session_factory,
):
    """assessment_versions.status CHECK rejects values outside the enum."""
    async with session_factory() as session:
        account_id = await _make_account(session, "vs@example.com")
        aid = await _insert_assessment(
            session, slug="vs-1", created_by=account_id
        )
        with pytest.raises(Exception):
            await _insert_version(
                session,
                assessment_id=aid,
                status="frozen_solid",
                drafted_by=account_id,
            )


@pytest.mark.anyio
async def test_assessment_questions_kind_check_rejects_invalid(
    session_factory,
):
    """assessment_questions.kind CHECK rejects values outside the enum."""
    async with session_factory() as session:
        account_id = await _make_account(session, "qk@example.com")
        aid = await _insert_assessment(
            session, slug="qk-1", created_by=account_id
        )
        vid = await _insert_version(
            session, assessment_id=aid, drafted_by=account_id
        )
        with pytest.raises(Exception):
            await session.execute(
                text(
                    "INSERT INTO assessment_questions "
                    "(version_id, position, prompt, kind, rubric_json) "
                    "VALUES (:vid, 1, 'p', 'invalid_kind', '{}')"
                ),
                {"vid": vid},
            )


@pytest.mark.anyio
async def test_assessment_reviews_action_check_rejects_invalid(
    session_factory,
):
    """assessment_reviews.action CHECK rejects values outside the enum."""
    async with session_factory() as session:
        account_id = await _make_account(session, "ra@example.com")
        aid = await _insert_assessment(
            session, slug="ra-1", created_by=account_id
        )
        vid = await _insert_version(
            session, assessment_id=aid, drafted_by=account_id
        )
        with pytest.raises(Exception):
            await session.execute(
                text(
                    "INSERT INTO assessment_reviews "
                    "(version_id, reviewer_id, action, comment, created_at) "
                    "VALUES (:vid, :rid, 'noped', 'no', :ts)"
                ),
                {
                    "vid": vid,
                    "rid": account_id,
                    "ts": "2026-05-07T00:00:00Z",
                },
            )


# ---------------------------------------------------------------------------
# UNIQUE constraints
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_assessment_versions_unique_assessment_version_number(
    session_factory,
):
    """UNIQUE(assessment_id, version_number) blocks duplicate versions."""
    async with session_factory() as session:
        account_id = await _make_account(session, "uv@example.com")
        aid = await _insert_assessment(
            session, slug="uv-1", created_by=account_id
        )
        await _insert_version(
            session,
            assessment_id=aid,
            version_number=1,
            drafted_by=account_id,
        )
        with pytest.raises(Exception):
            await _insert_version(
                session,
                assessment_id=aid,
                version_number=1,
                drafted_by=account_id,
            )


@pytest.mark.anyio
async def test_assessment_questions_unique_version_position(session_factory):
    """UNIQUE(version_id, position) blocks duplicate question positions."""
    async with session_factory() as session:
        account_id = await _make_account(session, "uq@example.com")
        aid = await _insert_assessment(
            session, slug="uq-1", created_by=account_id
        )
        vid = await _insert_version(
            session, assessment_id=aid, drafted_by=account_id
        )
        await session.execute(
            text(
                "INSERT INTO assessment_questions "
                "(version_id, position, prompt, kind, rubric_json) "
                "VALUES (:vid, 1, 'first', 'mcq', '{}')"
            ),
            {"vid": vid},
        )
        with pytest.raises(Exception):
            await session.execute(
                text(
                    "INSERT INTO assessment_questions "
                    "(version_id, position, prompt, kind, rubric_json) "
                    "VALUES (:vid, 1, 'duplicate', 'mcq', '{}')"
                ),
                {"vid": vid},
            )


@pytest.mark.anyio
async def test_assessments_slug_is_unique(session_factory):
    """assessments.slug UNIQUE blocks duplicate slugs."""
    async with session_factory() as session:
        account_id = await _make_account(session, "us@example.com")
        await _insert_assessment(
            session, slug="dupe", created_by=account_id
        )
        with pytest.raises(Exception):
            await _insert_assessment(
                session, slug="dupe", created_by=account_id
            )


# ---------------------------------------------------------------------------
# Enum-tuple coverage (single source of truth)
# ---------------------------------------------------------------------------


def test_enum_tuples_match_spec():
    """ENUM tuples expose the canonical set of values for the app layer."""
    assert ASSESSMENT_KINDS == (
        "skill_probe",
        "situational",
        "knowledge_check",
        "work_sample",
    )
    assert ASSESSMENT_TRACKS == ("vocational", "dao_tech", "generic")
    assert ASSESSMENT_VERSION_STATUSES == (
        "draft",
        "in_review",
        "approved",
        "published",
        "retired",
        "rejected",
    )
    assert QUESTION_KINDS == ("mcq", "freeform", "code", "scenario")
    assert REVIEW_ACTIONS == ("approve", "reject", "request_revision")
