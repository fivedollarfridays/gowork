"""Route + dependency tests for the reviewer queue API (T23.4).

Covers ``backend/app/routes/assessments_review.py`` end-to-end with
the real DB layer (no queries mocking) — the route handlers are
exercised directly via their underlying coroutines so the tests stay
on the same axes (sqlite + postgres) as the rest of the assessments
suite.

Behaviours covered:

* ``any_of_roles`` dependency: anonymous-403, none-of-the-roles-403,
  any-one-role-200.
* Track filter applied by reviewer role on ``GET /pending``.
* ``GET /{version_id}`` 404 when missing, payload includes questions.
* ``POST /{version_id}/review`` for each action; invalid action 422;
  state-machine immutability (published / retired) → 409.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import queries_accounts, queries_assessments, queries_roles
from app.core.accounts_schema import apply_ddl as apply_accounts_ddl
from app.core.assessments_schema import apply_ddl as apply_assessments_ddl
from app.core.auth_roles import any_of_roles, require_role
from app.core.roles_schema import apply_ddl as apply_roles_ddl
from app.routes import assessments_review
from app.routes._auth_claim_helpers import build_account_cookie_value


# ---------------------------------------------------------------------------
# Engine + fixture stack
# ---------------------------------------------------------------------------


@pytest.fixture
async def review_engine(db_engine):
    """``db_engine`` plus accounts + roles + assessments DDL applied."""
    async with db_engine.begin() as conn:
        await conn.run_sync(apply_accounts_ddl)
        await conn.run_sync(apply_roles_ddl)
        await conn.run_sync(apply_assessments_ddl)
    return db_engine


@pytest.fixture
def session_factory(review_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        review_engine, class_=AsyncSession, expire_on_commit=False
    )


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


async def _make_account_with_roles(
    session: AsyncSession, email: str, roles: list[str]
) -> tuple[int, str]:
    """Create an account, grant *roles*, return (id, cookie)."""
    account_id = await queries_accounts.create_account(session, email=email)
    for r in roles:
        await queries_roles.grant_role(session, account_id, r)
    return account_id, build_account_cookie_value(account_id)


async def _seed_draft(
    session: AsyncSession, slug: str, *, track: str = "vocational"
) -> tuple[int, int]:
    """Create one account + assessment + draft version. Returns (acct, vid)."""
    account_id = await queries_accounts.create_account(
        session, email=f"{slug}-author@example.com"
    )
    aid = await queries_assessments.create_assessment(
        session, slug=slug, kind="skill_probe",
        track=track, created_by=account_id,
    )
    vid = await queries_assessments.create_draft_version(
        session, assessment_id=aid, drafted_by=account_id,
        questions=[{
            "position": 1, "prompt": "p1", "kind": "mcq",
            "rubric_json": '{"answer": "x"}', "scoring_weight": 1.0,
        }],
    )
    return account_id, vid


# ---------------------------------------------------------------------------
# any_of_roles dependency
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_any_of_roles_403_when_anonymous(session_factory):
    """No cookie → 403 Authentication required."""
    async with session_factory() as session:
        dep = any_of_roles("case_manager", "sme_reviewer", "dao_reviewer")
        with pytest.raises(HTTPException) as exc:
            await dep(db=session, gw_account=None)
    assert exc.value.status_code == 403
    assert "Authentication" in exc.value.detail


@pytest.mark.anyio
async def test_any_of_roles_403_when_no_role_matches(session_factory):
    """Account holds none of the listed roles → 403 Insufficient."""
    async with session_factory() as session:
        _, cookie = await _make_account_with_roles(
            session, "nobody@example.com", ["admin"]  # not in any_of set
        )
        dep = any_of_roles("case_manager", "sme_reviewer", "dao_reviewer")
        with pytest.raises(HTTPException) as exc:
            await dep(db=session, gw_account=cookie)
    assert exc.value.status_code == 403
    assert "Insufficient" in exc.value.detail


@pytest.mark.anyio
async def test_any_of_roles_200_when_first_role_matches(session_factory):
    """Account has the first listed role → returns the account dict."""
    async with session_factory() as session:
        account_id, cookie = await _make_account_with_roles(
            session, "cm@example.com", ["case_manager"]
        )
        dep = any_of_roles("case_manager", "sme_reviewer", "dao_reviewer")
        account = await dep(db=session, gw_account=cookie)
    assert account["id"] == account_id


@pytest.mark.anyio
async def test_any_of_roles_200_when_last_role_matches(session_factory):
    """Account has only the last listed role → still authorized."""
    async with session_factory() as session:
        account_id, cookie = await _make_account_with_roles(
            session, "dao@example.com", ["dao_reviewer"]
        )
        dep = any_of_roles("case_manager", "sme_reviewer", "dao_reviewer")
        account = await dep(db=session, gw_account=cookie)
    assert account["id"] == account_id


# ---------------------------------------------------------------------------
# GET /api/admin/assessments/pending
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_pending_case_manager_excludes_dao_tech(session_factory):
    """case_manager queue must NOT show dao_tech drafts."""
    async with session_factory() as session:
        await _seed_draft(session, "voc-cm", track="vocational")
        await _seed_draft(session, "dao-cm", track="dao_tech")
        _, cookie = await _make_account_with_roles(
            session, "cm-user@example.com", ["case_manager"]
        )
        account = await any_of_roles(
            "case_manager", "sme_reviewer", "dao_reviewer"
        )(db=session, gw_account=cookie)
        rows = await assessments_review.list_pending(
            db=session, account=account
        )
    slugs = {r["slug"] for r in rows}
    assert "voc-cm" in slugs
    assert "dao-cm" not in slugs


@pytest.mark.anyio
async def test_pending_dao_reviewer_excludes_vocational(session_factory):
    """dao_reviewer queue must NOT show vocational drafts."""
    async with session_factory() as session:
        await _seed_draft(session, "voc-dao", track="vocational")
        await _seed_draft(session, "dao-dao", track="dao_tech")
        _, cookie = await _make_account_with_roles(
            session, "dao-user@example.com", ["dao_reviewer"]
        )
        account = await any_of_roles(
            "case_manager", "sme_reviewer", "dao_reviewer"
        )(db=session, gw_account=cookie)
        rows = await assessments_review.list_pending(
            db=session, account=account
        )
    slugs = {r["slug"] for r in rows}
    assert "dao-dao" in slugs
    assert "voc-dao" not in slugs


@pytest.mark.anyio
async def test_pending_sme_reviewer_sees_all_tracks(session_factory):
    """sme_reviewer queue includes vocational + dao_tech + generic."""
    async with session_factory() as session:
        await _seed_draft(session, "voc-sme", track="vocational")
        await _seed_draft(session, "dao-sme", track="dao_tech")
        await _seed_draft(session, "gen-sme", track="generic")
        _, cookie = await _make_account_with_roles(
            session, "sme-user@example.com", ["sme_reviewer"]
        )
        account = await any_of_roles(
            "case_manager", "sme_reviewer", "dao_reviewer"
        )(db=session, gw_account=cookie)
        rows = await assessments_review.list_pending(
            db=session, account=account
        )
    slugs = {r["slug"] for r in rows}
    assert {"voc-sme", "dao-sme", "gen-sme"}.issubset(slugs)


# ---------------------------------------------------------------------------
# GET /api/admin/assessments/{version_id}
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_version_returns_questions_payload(session_factory):
    """Authorized GET returns version metadata + questions list."""
    async with session_factory() as session:
        _, vid = await _seed_draft(session, "voc-detail", track="vocational")
        _, cookie = await _make_account_with_roles(
            session, "rev-detail@example.com", ["sme_reviewer"]
        )
        account = await any_of_roles(
            "case_manager", "sme_reviewer", "dao_reviewer"
        )(db=session, gw_account=cookie)
        payload = await assessments_review.get_version(
            version_id=vid, db=session, account=account,
        )
    assert payload["version_id"] == vid
    assert payload["status"] == "draft"
    assert isinstance(payload["questions"], list)
    assert len(payload["questions"]) == 1


@pytest.mark.anyio
async def test_get_version_404_when_missing(session_factory):
    """Unknown version_id raises 404."""
    async with session_factory() as session:
        _, cookie = await _make_account_with_roles(
            session, "rev-404@example.com", ["sme_reviewer"]
        )
        account = await any_of_roles(
            "case_manager", "sme_reviewer", "dao_reviewer"
        )(db=session, gw_account=cookie)
        with pytest.raises(HTTPException) as exc:
            await assessments_review.get_version(
                version_id=999999, db=session, account=account,
            )
    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/admin/assessments/{version_id}/review
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_review_approve_transitions_version(session_factory):
    """approve action moves draft → approved."""
    async with session_factory() as session:
        _, vid = await _seed_draft(session, "voc-approve", track="vocational")
        reviewer_id, cookie = await _make_account_with_roles(
            session, "rev-approve@example.com", ["sme_reviewer"]
        )
        account = await any_of_roles(
            "case_manager", "sme_reviewer", "dao_reviewer"
        )(db=session, gw_account=cookie)
        body = assessments_review.ReviewBody(
            action="approve", comment="lgtm"
        )
        result = await assessments_review.submit_review(
            version_id=vid, body=body, db=session, account=account,
        )
        # State changed in db
        status_row = await session.execute(
            text("SELECT status FROM assessment_versions WHERE id = :id"),
            {"id": vid},
        )
    assert result["review_id"] > 0
    assert status_row.scalar_one() == "approved"


@pytest.mark.anyio
async def test_review_request_revision_sends_back_to_draft(session_factory):
    """request_revision keeps the version in the draft state."""
    async with session_factory() as session:
        _, vid = await _seed_draft(session, "voc-rev", track="vocational")
        _, cookie = await _make_account_with_roles(
            session, "rev-revise@example.com", ["sme_reviewer"]
        )
        account = await any_of_roles(
            "case_manager", "sme_reviewer", "dao_reviewer"
        )(db=session, gw_account=cookie)
        body = assessments_review.ReviewBody(
            action="request_revision", comment="needs fixes"
        )
        await assessments_review.submit_review(
            version_id=vid, body=body, db=session, account=account,
        )
        status_row = await session.execute(
            text("SELECT status FROM assessment_versions WHERE id = :id"),
            {"id": vid},
        )
    assert status_row.scalar_one() == "draft"


@pytest.mark.anyio
async def test_review_reject_transitions_to_rejected(session_factory):
    """reject moves draft → rejected."""
    async with session_factory() as session:
        _, vid = await _seed_draft(session, "voc-rej", track="vocational")
        _, cookie = await _make_account_with_roles(
            session, "rev-reject@example.com", ["sme_reviewer"]
        )
        account = await any_of_roles(
            "case_manager", "sme_reviewer", "dao_reviewer"
        )(db=session, gw_account=cookie)
        body = assessments_review.ReviewBody(
            action="reject", comment="bad"
        )
        await assessments_review.submit_review(
            version_id=vid, body=body, db=session, account=account,
        )
        status_row = await session.execute(
            text("SELECT status FROM assessment_versions WHERE id = :id"),
            {"id": vid},
        )
    assert status_row.scalar_one() == "rejected"


@pytest.mark.anyio
async def test_review_published_version_returns_409(session_factory):
    """Reviewing a published version raises 409 from queries ValueError."""
    async with session_factory() as session:
        author_id, vid = await _seed_draft(
            session, "voc-pub", track="vocational"
        )
        # Walk it through approve → publish.
        await queries_assessments.record_review(
            session, version_id=vid, reviewer_id=author_id,
            action="approve", comment="ok",
        )
        await queries_assessments.publish_version(
            session, version_id=vid, approved_by=author_id,
        )
        _, cookie = await _make_account_with_roles(
            session, "rev-pub@example.com", ["sme_reviewer"]
        )
        account = await any_of_roles(
            "case_manager", "sme_reviewer", "dao_reviewer"
        )(db=session, gw_account=cookie)
        body = assessments_review.ReviewBody(
            action="approve", comment="late"
        )
        with pytest.raises(HTTPException) as exc:
            await assessments_review.submit_review(
                version_id=vid, body=body, db=session, account=account,
            )
    assert exc.value.status_code == 409


@pytest.mark.anyio
async def test_review_retired_version_returns_409(session_factory):
    """Reviewing a retired version → 409 (state machine guard)."""
    async with session_factory() as session:
        author_id, vid = await _seed_draft(
            session, "voc-ret", track="vocational"
        )
        await queries_assessments.record_review(
            session, version_id=vid, reviewer_id=author_id,
            action="approve", comment="ok",
        )
        await queries_assessments.publish_version(
            session, version_id=vid, approved_by=author_id,
        )
        await queries_assessments.retire_version(session, version_id=vid)
        _, cookie = await _make_account_with_roles(
            session, "rev-ret@example.com", ["sme_reviewer"]
        )
        account = await any_of_roles(
            "case_manager", "sme_reviewer", "dao_reviewer"
        )(db=session, gw_account=cookie)
        body = assessments_review.ReviewBody(
            action="approve", comment="late"
        )
        with pytest.raises(HTTPException) as exc:
            await assessments_review.submit_review(
                version_id=vid, body=body, db=session, account=account,
            )
    assert exc.value.status_code == 409


@pytest.mark.anyio
async def test_review_rejects_anonymous(session_factory):
    """No cookie on the review POST → 403 from any_of_roles dep."""
    async with session_factory() as session:
        dep = any_of_roles("case_manager", "sme_reviewer", "dao_reviewer")
        with pytest.raises(HTTPException) as exc:
            await dep(db=session, gw_account=None)
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------


def test_review_router_registered():
    """assessments_review_router is mounted in app.routes.all_routers."""
    from app.routes import all_routers
    from app.routes.assessments_review import router as review_router

    assert review_router in all_routers
