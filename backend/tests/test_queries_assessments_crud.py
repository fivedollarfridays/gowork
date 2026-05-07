"""CRUD tests for :mod:`app.core.queries_assessments` (T23.2, part 1).

This file owns the raw-CRUD helpers:

* ``create_assessment`` — happy + invalid-kind / invalid-track
  ``ValueError`` + duplicate-slug ``IntegrityError``.
* ``create_draft_version`` — first version returns 1, second
  increments, all questions land, atomicity on question failure.
* ``get_version_with_questions`` — ordered by position, None on
  missing.

State-machine flows (record_review / publish / retire / queue / public
fetch) live in ``test_queries_assessments_state.py`` to keep both
files under the per-file size limit.

All tests use the shared ``session_factory`` fixture so they execute
on both the sqlite (aiosqlite) and postgres (asyncpg) axes.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.core import queries_assessments

# Bring shared fixtures + helpers into module scope so pytest discovers
# the fixtures and the test bodies can call the helper functions.
from tests._assessments_test_fixtures import (  # noqa: F401
    assessments_engine,
    session_factory,
    make_account,
    question,
    seed_assessment_with_draft,
)


# ---------------------------------------------------------------------------
# create_assessment
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_assessment_happy_path(session_factory):
    """Returns a positive integer id; row is queryable."""
    async with session_factory() as session:
        account_id = await make_account(session, "ca@example.com")
        aid = await queries_assessments.create_assessment(
            session,
            slug="probe-1",
            kind="skill_probe",
            track="vocational",
            created_by=account_id,
        )
        assert isinstance(aid, int) and aid > 0
        result = await session.execute(
            text("SELECT slug, kind, track FROM assessments WHERE id = :id"),
            {"id": aid},
        )
        row = result.first()
        assert row is not None
        assert row._mapping["slug"] == "probe-1"
        assert row._mapping["kind"] == "skill_probe"
        assert row._mapping["track"] == "vocational"


@pytest.mark.anyio
async def test_create_assessment_invalid_kind_raises_value_error(session_factory):
    """Unknown kind hits the Python tuple guard, not the CHECK clause."""
    async with session_factory() as session:
        account_id = await make_account(session, "bk@example.com")
        with pytest.raises(ValueError, match="kind"):
            await queries_assessments.create_assessment(
                session,
                slug="bad-kind",
                kind="not_a_kind",
                track="vocational",
                created_by=account_id,
            )


@pytest.mark.anyio
async def test_create_assessment_invalid_track_raises_value_error(session_factory):
    """Unknown track hits the Python tuple guard, not the CHECK clause."""
    async with session_factory() as session:
        account_id = await make_account(session, "bt@example.com")
        with pytest.raises(ValueError, match="track"):
            await queries_assessments.create_assessment(
                session,
                slug="bad-track",
                kind="skill_probe",
                track="space_force",
                created_by=account_id,
            )


@pytest.mark.anyio
async def test_create_assessment_duplicate_slug_raises_integrity(session_factory):
    """UNIQUE(slug) surfaces as the dialect's IntegrityError."""
    async with session_factory() as session:
        account_id = await make_account(session, "ds@example.com")
        await queries_assessments.create_assessment(
            session,
            slug="dupe",
            kind="skill_probe",
            track="vocational",
            created_by=account_id,
        )
        with pytest.raises(Exception):
            await queries_assessments.create_assessment(
                session,
                slug="dupe",
                kind="skill_probe",
                track="vocational",
                created_by=account_id,
            )


# ---------------------------------------------------------------------------
# create_draft_version
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_draft_version_first_version_is_one(session_factory):
    """First version of an assessment lands at version_number=1."""
    async with session_factory() as session:
        _, _, vid = await seed_assessment_with_draft(session, slug="dv-first")
        result = await session.execute(
            text(
                "SELECT version_number, status FROM assessment_versions "
                "WHERE id = :id"
            ),
            {"id": vid},
        )
        row = result.first()
        assert row is not None
        assert int(row._mapping["version_number"]) == 1
        assert row._mapping["status"] == "draft"


@pytest.mark.anyio
async def test_create_draft_version_second_increments(session_factory):
    """Second draft on the same assessment lands at version_number=2."""
    async with session_factory() as session:
        account_id, aid, _ = await seed_assessment_with_draft(
            session, slug="dv-second"
        )
        vid2 = await queries_assessments.create_draft_version(
            session,
            assessment_id=aid,
            drafted_by=account_id,
            questions=[question(1)],
        )
        result = await session.execute(
            text(
                "SELECT version_number FROM assessment_versions WHERE id = :id"
            ),
            {"id": vid2},
        )
        assert int(result.scalar_one()) == 2


@pytest.mark.anyio
async def test_create_draft_version_inserts_questions(session_factory):
    """All supplied questions land + carry their position + scoring_weight."""
    async with session_factory() as session:
        _, _, vid = await seed_assessment_with_draft(
            session, slug="dv-q", question_count=3
        )
        result = await session.execute(
            text(
                "SELECT position, prompt, kind, scoring_weight "
                "FROM assessment_questions WHERE version_id = :v "
                "ORDER BY position"
            ),
            {"v": vid},
        )
        rows = list(result)
        assert len(rows) == 3
        assert [r._mapping["position"] for r in rows] == [1, 2, 3]
        assert all(r._mapping["kind"] == "mcq" for r in rows)


@pytest.mark.anyio
async def test_create_draft_version_atomic_on_question_failure(session_factory):
    """A bad question tuple rolls back the version row too."""
    async with session_factory() as session:
        account_id = await make_account(session, "atomic@example.com")
        aid = await queries_assessments.create_assessment(
            session,
            slug="atomic",
            kind="skill_probe",
            track="vocational",
            created_by=account_id,
        )
        bad_questions = [question(1), question(1)]  # dup position -> Integrity
        with pytest.raises(Exception):
            await queries_assessments.create_draft_version(
                session,
                assessment_id=aid,
                drafted_by=account_id,
                questions=bad_questions,
            )
    async with session_factory() as session:
        result = await session.execute(
            text(
                "SELECT COUNT(*) FROM assessment_versions "
                "WHERE assessment_id = :a"
            ),
            {"a": aid},
        )
        assert int(result.scalar_one()) == 0


# ---------------------------------------------------------------------------
# get_version_with_questions
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_version_with_questions_returns_ordered(session_factory):
    """Questions come back sorted by position even if inserted out of order."""
    async with session_factory() as session:
        account_id = await make_account(session, "gv@example.com")
        aid = await queries_assessments.create_assessment(
            session,
            slug="gv-1",
            kind="skill_probe",
            track="vocational",
            created_by=account_id,
        )
        vid = await queries_assessments.create_draft_version(
            session,
            assessment_id=aid,
            drafted_by=account_id,
            questions=[question(3), question(1), question(2)],
        )
        payload = await queries_assessments.get_version_with_questions(
            session, version_id=vid
        )
        assert payload is not None
        assert payload["version_id"] == vid
        assert payload["status"] == "draft"
        positions = [q["position"] for q in payload["questions"]]
        assert positions == [1, 2, 3]


@pytest.mark.anyio
async def test_get_version_with_questions_missing_returns_none(session_factory):
    async with session_factory() as session:
        result = await queries_assessments.get_version_with_questions(
            session, version_id=99999
        )
        assert result is None
