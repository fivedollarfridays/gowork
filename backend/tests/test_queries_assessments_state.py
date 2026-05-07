"""State-machine tests for :mod:`app.core.queries_assessments` (T23.2, part 2).

This file owns the state-transition flows:

* ``list_pending_reviews`` — track-aware filter per reviewer role,
  with status filter excluding published / retired / rejected.
* ``record_review`` — every action transition + immutability of
  published / retired versions.
* ``publish_version`` — guards status==approved, sets published_at.
* ``get_published_version`` — returns latest published; rubric_json
  EXCLUDED from the public payload.
* ``retire_version`` — happy path + double-retire ValueError.

Raw CRUD lives in ``test_queries_assessments_crud.py`` to keep both
files under the per-file size limit.

All tests use the shared ``session_factory`` fixture so they execute
on both the sqlite (aiosqlite) and postgres (asyncpg) axes.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import queries_assessments

from tests._assessments_test_fixtures import (  # noqa: F401
    assessments_engine,
    session_factory,
    approve_version,
    question,
    seed_assessment_with_draft,
)


# ---------------------------------------------------------------------------
# list_pending_reviews — local seed helper
# ---------------------------------------------------------------------------


async def _seed_for_role_filter(session: AsyncSession) -> dict:
    """Seed one draft per track plus one published row to verify filtering.

    Returns the dict of slug -> version_id so the assertions can pin
    down exactly which versions surface.
    """
    out: dict[str, int] = {}
    for slug, track in (
        ("voc-1", "vocational"),
        ("dao-1", "dao_tech"),
        ("gen-1", "generic"),
    ):
        _, _, vid = await seed_assessment_with_draft(
            session, slug=slug, track=track
        )
        out[slug] = vid
    # Add a published row in 'vocational' that must NEVER appear.
    account_id, _, vid_pub = await seed_assessment_with_draft(
        session, slug="voc-pub", track="vocational"
    )
    await approve_version(session, vid_pub, account_id)
    await queries_assessments.publish_version(
        session, version_id=vid_pub, approved_by=account_id
    )
    out["voc-pub"] = vid_pub
    return out


@pytest.mark.anyio
async def test_list_pending_reviews_case_manager_sees_voc_and_generic(session_factory):
    async with session_factory() as session:
        seeds = await _seed_for_role_filter(session)
        rows = await queries_assessments.list_pending_reviews(
            session, reviewer_role="case_manager"
        )
        slugs = {r["slug"] for r in rows}
        assert seeds["voc-1"] in {r["version_id"] for r in rows}
        assert "voc-1" in slugs and "gen-1" in slugs
        assert "dao-1" not in slugs
        assert "voc-pub" not in slugs


@pytest.mark.anyio
async def test_list_pending_reviews_dao_reviewer_sees_dao_and_generic(session_factory):
    async with session_factory() as session:
        await _seed_for_role_filter(session)
        rows = await queries_assessments.list_pending_reviews(
            session, reviewer_role="dao_reviewer"
        )
        slugs = {r["slug"] for r in rows}
        assert "dao-1" in slugs and "gen-1" in slugs
        assert "voc-1" not in slugs


@pytest.mark.anyio
async def test_list_pending_reviews_sme_reviewer_sees_all(session_factory):
    async with session_factory() as session:
        await _seed_for_role_filter(session)
        rows = await queries_assessments.list_pending_reviews(
            session, reviewer_role="sme_reviewer"
        )
        slugs = {r["slug"] for r in rows}
        assert {"voc-1", "dao-1", "gen-1"}.issubset(slugs)
        assert "voc-pub" not in slugs


@pytest.mark.anyio
async def test_list_pending_reviews_unknown_role_returns_empty(session_factory):
    async with session_factory() as session:
        await _seed_for_role_filter(session)
        rows = await queries_assessments.list_pending_reviews(
            session, reviewer_role="random_role"
        )
        assert rows == []


@pytest.mark.anyio
async def test_list_pending_reviews_excludes_rejected_and_retired(session_factory):
    """Rejected + retired versions never appear in the queue."""
    async with session_factory() as session:
        # Rejected
        account_id, _, vid_rej = await seed_assessment_with_draft(
            session, slug="rej-1", track="vocational"
        )
        await queries_assessments.record_review(
            session,
            version_id=vid_rej,
            reviewer_id=account_id,
            action="reject",
            comment="no",
        )
        # Approved + published + retired
        _, _, vid_ret = await seed_assessment_with_draft(
            session, slug="ret-1", track="vocational"
        )
        await approve_version(session, vid_ret, account_id)
        await queries_assessments.publish_version(
            session, version_id=vid_ret, approved_by=account_id
        )
        await queries_assessments.retire_version(session, version_id=vid_ret)
        rows = await queries_assessments.list_pending_reviews(
            session, reviewer_role="sme_reviewer"
        )
        slugs = {r["slug"] for r in rows}
        assert "rej-1" not in slugs and "ret-1" not in slugs


# ---------------------------------------------------------------------------
# record_review state transitions
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_record_review_approve_transitions_to_approved(session_factory):
    async with session_factory() as session:
        account_id, _, vid = await seed_assessment_with_draft(
            session, slug="rr-app"
        )
        review_id = await queries_assessments.record_review(
            session,
            version_id=vid,
            reviewer_id=account_id,
            action="approve",
            comment="solid",
        )
        assert isinstance(review_id, int) and review_id > 0
        result = await session.execute(
            text(
                "SELECT status, reviewed_by FROM assessment_versions "
                "WHERE id = :id"
            ),
            {"id": vid},
        )
        row = result.first()
        assert row._mapping["status"] == "approved"
        assert int(row._mapping["reviewed_by"]) == account_id


@pytest.mark.anyio
async def test_record_review_reject_transitions_to_rejected(session_factory):
    async with session_factory() as session:
        account_id, _, vid = await seed_assessment_with_draft(
            session, slug="rr-rej"
        )
        await queries_assessments.record_review(
            session,
            version_id=vid,
            reviewer_id=account_id,
            action="reject",
            comment="no",
        )
        result = await session.execute(
            text("SELECT status FROM assessment_versions WHERE id = :id"),
            {"id": vid},
        )
        assert result.scalar_one() == "rejected"


@pytest.mark.anyio
async def test_record_review_request_revision_returns_to_draft(session_factory):
    """request_revision is an action — version returns to draft.

    The schema's version-status enum (T23.1) does not include
    ``request_revision``; the action sends the version back to the
    author by setting ``status='draft'`` again.
    """
    async with session_factory() as session:
        account_id, _, vid = await seed_assessment_with_draft(
            session, slug="rr-rev"
        )
        await queries_assessments.record_review(
            session,
            version_id=vid,
            reviewer_id=account_id,
            action="request_revision",
            comment="needs work",
        )
        result = await session.execute(
            text("SELECT status FROM assessment_versions WHERE id = :id"),
            {"id": vid},
        )
        assert result.scalar_one() == "draft"


@pytest.mark.anyio
async def test_record_review_on_published_raises_value_error(session_factory):
    """Published is immutable — record_review raises ValueError."""
    async with session_factory() as session:
        account_id, _, vid = await seed_assessment_with_draft(
            session, slug="rr-pub"
        )
        await approve_version(session, vid, account_id)
        await queries_assessments.publish_version(
            session, version_id=vid, approved_by=account_id
        )
        with pytest.raises(ValueError, match="published"):
            await queries_assessments.record_review(
                session,
                version_id=vid,
                reviewer_id=account_id,
                action="approve",
                comment="too late",
            )


@pytest.mark.anyio
async def test_record_review_on_retired_raises_value_error(session_factory):
    async with session_factory() as session:
        account_id, _, vid = await seed_assessment_with_draft(
            session, slug="rr-ret"
        )
        await approve_version(session, vid, account_id)
        await queries_assessments.publish_version(
            session, version_id=vid, approved_by=account_id
        )
        await queries_assessments.retire_version(session, version_id=vid)
        with pytest.raises(ValueError):
            await queries_assessments.record_review(
                session,
                version_id=vid,
                reviewer_id=account_id,
                action="approve",
                comment="zombie",
            )


@pytest.mark.anyio
async def test_record_review_invalid_action_raises_value_error(session_factory):
    async with session_factory() as session:
        account_id, _, vid = await seed_assessment_with_draft(
            session, slug="rr-bad"
        )
        with pytest.raises(ValueError, match="action"):
            await queries_assessments.record_review(
                session,
                version_id=vid,
                reviewer_id=account_id,
                action="ghost",
                comment="?",
            )


# ---------------------------------------------------------------------------
# publish_version
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_publish_version_happy_path_sets_published_at(session_factory):
    async with session_factory() as session:
        account_id, _, vid = await seed_assessment_with_draft(
            session, slug="pv-ok"
        )
        await approve_version(session, vid, account_id)
        await queries_assessments.publish_version(
            session, version_id=vid, approved_by=account_id
        )
        result = await session.execute(
            text(
                "SELECT status, published_at, approved_by "
                "FROM assessment_versions WHERE id = :id"
            ),
            {"id": vid},
        )
        row = result.first()
        assert row._mapping["status"] == "published"
        assert row._mapping["published_at"] is not None
        assert int(row._mapping["approved_by"]) == account_id


@pytest.mark.anyio
async def test_publish_version_on_draft_raises_value_error(session_factory):
    async with session_factory() as session:
        account_id, _, vid = await seed_assessment_with_draft(
            session, slug="pv-draft"
        )
        with pytest.raises(ValueError, match="approved"):
            await queries_assessments.publish_version(
                session, version_id=vid, approved_by=account_id
            )


@pytest.mark.anyio
async def test_publish_version_missing_raises_value_error(session_factory):
    async with session_factory() as session:
        with pytest.raises(ValueError):
            await queries_assessments.publish_version(
                session, version_id=99999, approved_by=1
            )


# ---------------------------------------------------------------------------
# get_published_version
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_published_version_returns_latest(session_factory):
    """Two published versions: helper returns the higher version_number."""
    async with session_factory() as session:
        account_id, aid, vid1 = await seed_assessment_with_draft(
            session, slug="latest"
        )
        await approve_version(session, vid1, account_id)
        await queries_assessments.publish_version(
            session, version_id=vid1, approved_by=account_id
        )
        vid2 = await queries_assessments.create_draft_version(
            session,
            assessment_id=aid,
            drafted_by=account_id,
            questions=[question(1)],
        )
        await approve_version(session, vid2, account_id)
        await queries_assessments.publish_version(
            session, version_id=vid2, approved_by=account_id
        )
        payload = await queries_assessments.get_published_version(
            session, slug="latest"
        )
        assert payload is not None
        assert payload["version_id"] == vid2
        assert payload["version_number"] == 2


@pytest.mark.anyio
async def test_get_published_version_excludes_rubric_json(session_factory):
    """Public payload must NEVER include rubric_json."""
    async with session_factory() as session:
        account_id, _, vid = await seed_assessment_with_draft(
            session, slug="no-rubric"
        )
        await approve_version(session, vid, account_id)
        await queries_assessments.publish_version(
            session, version_id=vid, approved_by=account_id
        )
        payload = await queries_assessments.get_published_version(
            session, slug="no-rubric"
        )
        assert payload is not None
        for q in payload["questions"]:
            assert "rubric_json" not in q


@pytest.mark.anyio
async def test_get_published_version_no_published_returns_none(session_factory):
    """If no version was ever published, helper returns None."""
    async with session_factory() as session:
        await seed_assessment_with_draft(session, slug="never-pub")
        payload = await queries_assessments.get_published_version(
            session, slug="never-pub"
        )
        assert payload is None


@pytest.mark.anyio
async def test_get_published_version_unknown_slug_returns_none(session_factory):
    async with session_factory() as session:
        payload = await queries_assessments.get_published_version(
            session, slug="does-not-exist"
        )
        assert payload is None


# ---------------------------------------------------------------------------
# retire_version
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_retire_version_happy_path(session_factory):
    async with session_factory() as session:
        account_id, _, vid = await seed_assessment_with_draft(
            session, slug="ret-ok"
        )
        await approve_version(session, vid, account_id)
        await queries_assessments.publish_version(
            session, version_id=vid, approved_by=account_id
        )
        await queries_assessments.retire_version(session, version_id=vid)
        result = await session.execute(
            text(
                "SELECT status, retired_at FROM assessment_versions "
                "WHERE id = :id"
            ),
            {"id": vid},
        )
        row = result.first()
        assert row._mapping["status"] == "retired"
        assert row._mapping["retired_at"] is not None


@pytest.mark.anyio
async def test_retire_version_already_retired_raises_value_error(session_factory):
    async with session_factory() as session:
        account_id, _, vid = await seed_assessment_with_draft(
            session, slug="ret-twice"
        )
        await approve_version(session, vid, account_id)
        await queries_assessments.publish_version(
            session, version_id=vid, approved_by=account_id
        )
        await queries_assessments.retire_version(session, version_id=vid)
        with pytest.raises(ValueError, match="retired"):
            await queries_assessments.retire_version(session, version_id=vid)


@pytest.mark.anyio
async def test_retire_version_missing_raises_value_error(session_factory):
    async with session_factory() as session:
        with pytest.raises(ValueError):
            await queries_assessments.retire_version(session, version_id=99999)
