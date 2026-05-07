"""Route tests for the publish endpoint of the assessment authoring pipeline (T23.5).

Covers ``POST /api/admin/assessments/{version_id}/publish`` end-to-end
with the real DB layer. The publish surface is narrower than the
reviewer queue: only ``admin`` can call it (``require_role("admin")``
not ``any_of_roles`` over the reviewer triplet).

Behaviours covered
------------------

* approve-then-publish happy path: drives the full state-machine path
  (draft -> approved -> published) and returns the public URL.
* publish-without-approve -> 409: state-machine guard from
  :func:`queries_assessments.publish_version`.
* double-publish -> 409: a second call on a published version is also
  blocked by the same guard (current_status != approved).
* role enforcement: sme_reviewer / case_manager / dao_reviewer all 403,
  anonymous 403. Only admin can publish.
* provenance row inspection: the four provenance columns
  (``drafted_by``, ``reviewed_by``, ``approved_by``, ``published_at``)
  are all non-null on the published row — the load-bearing charter
  invariant for assessment publication.
* record_review on a published version returns 409 (T23.2 guard
  re-asserted from this surface so future refactors don't regress it).
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
# Engine + fixture stack (mirrors test_assessments_review.py)
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
# Helpers
# ---------------------------------------------------------------------------


async def _make_account_with_roles(
    session: AsyncSession, email: str, roles: list[str]
) -> tuple[int, str]:
    """Create an account, grant *roles*, return (id, cookie)."""
    account_id = await queries_accounts.create_account(session, email=email)
    for r in roles:
        await queries_roles.grant_role(session, account_id, r)
    return account_id, build_account_cookie_value(account_id)


async def _seed_approved_version(
    session: AsyncSession, slug: str
) -> tuple[int, int, int, int]:
    """Create assessment + draft + record an approve review.

    Returns ``(author_id, reviewer_id, assessment_id, version_id)`` on
    a version whose status is now ``approved`` and which has both
    ``drafted_by`` and ``reviewed_by`` populated.
    """
    author_id = await queries_accounts.create_account(
        session, email=f"{slug}-author@example.com"
    )
    reviewer_id = await queries_accounts.create_account(
        session, email=f"{slug}-reviewer@example.com"
    )
    aid = await queries_assessments.create_assessment(
        session, slug=slug, kind="skill_probe",
        track="vocational", created_by=author_id,
    )
    vid = await queries_assessments.create_draft_version(
        session, assessment_id=aid, drafted_by=author_id,
        questions=[{
            "position": 1, "prompt": "p1", "kind": "mcq",
            "rubric_json": '{"answer": "x"}', "scoring_weight": 1.0,
        }],
    )
    await queries_assessments.record_review(
        session, version_id=vid, reviewer_id=reviewer_id,
        action="approve", comment="ok",
    )
    return author_id, reviewer_id, aid, vid


async def _seed_draft_only(
    session: AsyncSession, slug: str
) -> tuple[int, int]:
    """Create author + assessment + draft (no review yet). Returns (author, vid)."""
    author_id = await queries_accounts.create_account(
        session, email=f"{slug}-author@example.com"
    )
    aid = await queries_assessments.create_assessment(
        session, slug=slug, kind="skill_probe",
        track="vocational", created_by=author_id,
    )
    vid = await queries_assessments.create_draft_version(
        session, assessment_id=aid, drafted_by=author_id,
        questions=[{
            "position": 1, "prompt": "p1", "kind": "mcq",
            "rubric_json": '{"answer": "x"}', "scoring_weight": 1.0,
        }],
    )
    return author_id, vid


async def _resolve_admin_account(
    session: AsyncSession, cookie: str,
) -> dict:
    """Run the admin require_role dependency to get the account dict."""
    return await require_role("admin")(db=session, gw_account=cookie)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_publish_approved_version_returns_public_url(session_factory):
    """admin publish on an approved version returns the expected payload."""
    async with session_factory() as session:
        _, _, aid, vid = await _seed_approved_version(session, "voc-pub-ok")
        _, cookie = await _make_account_with_roles(
            session, "admin-pub-ok@example.com", ["admin"]
        )
        account = await _resolve_admin_account(session, cookie)
        result = await assessments_review.publish_version_endpoint(
            version_id=vid, db=session, account=account,
        )
    assert result["assessment_id"] == aid
    assert result["version_id"] == vid
    assert result["slug"] == "voc-pub-ok"
    assert result["version_number"] == 1
    assert result["published_at"] is not None
    assert result["public_url"] == "/api/assessments/voc-pub-ok"


@pytest.mark.anyio
async def test_publish_provenance_all_four_columns_non_null(session_factory):
    """drafted_by + reviewed_by + approved_by + published_at all populated."""
    async with session_factory() as session:
        author_id, reviewer_id, _, vid = await _seed_approved_version(
            session, "voc-prov"
        )
        admin_id, cookie = await _make_account_with_roles(
            session, "admin-prov@example.com", ["admin"]
        )
        account = await _resolve_admin_account(session, cookie)
        await assessments_review.publish_version_endpoint(
            version_id=vid, db=session, account=account,
        )
        row = await session.execute(
            text(
                "SELECT drafted_by, reviewed_by, approved_by, "
                "published_at, status "
                "FROM assessment_versions WHERE id = :id"
            ),
            {"id": vid},
        )
        provenance = dict(row.first()._mapping)
    assert provenance["drafted_by"] == author_id
    assert provenance["reviewed_by"] == reviewer_id
    assert provenance["approved_by"] == admin_id
    assert provenance["published_at"] is not None
    assert provenance["status"] == "published"


# ---------------------------------------------------------------------------
# 409 guards
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_publish_without_approve_returns_409(session_factory):
    """Publishing a draft (never approved) raises 409."""
    async with session_factory() as session:
        _, vid = await _seed_draft_only(session, "voc-no-approve")
        _, cookie = await _make_account_with_roles(
            session, "admin-no-approve@example.com", ["admin"]
        )
        account = await _resolve_admin_account(session, cookie)
        with pytest.raises(HTTPException) as exc:
            await assessments_review.publish_version_endpoint(
                version_id=vid, db=session, account=account,
            )
    assert exc.value.status_code == 409
    assert "approved" in exc.value.detail.lower()


@pytest.mark.anyio
async def test_publish_already_published_returns_409(session_factory):
    """Double-publish blocked: second call on published version → 409."""
    async with session_factory() as session:
        _, _, _, vid = await _seed_approved_version(session, "voc-double")
        _, cookie = await _make_account_with_roles(
            session, "admin-double@example.com", ["admin"]
        )
        account = await _resolve_admin_account(session, cookie)
        # First publish succeeds.
        await assessments_review.publish_version_endpoint(
            version_id=vid, db=session, account=account,
        )
        # Second call must fail with 409.
        with pytest.raises(HTTPException) as exc:
            await assessments_review.publish_version_endpoint(
                version_id=vid, db=session, account=account,
            )
    assert exc.value.status_code == 409


@pytest.mark.anyio
async def test_publish_unknown_version_returns_409(session_factory):
    """Non-existent version_id → 409 from publish_version ValueError."""
    async with session_factory() as session:
        _, cookie = await _make_account_with_roles(
            session, "admin-missing@example.com", ["admin"]
        )
        account = await _resolve_admin_account(session, cookie)
        with pytest.raises(HTTPException) as exc:
            await assessments_review.publish_version_endpoint(
                version_id=999999, db=session, account=account,
            )
    assert exc.value.status_code == 409


# ---------------------------------------------------------------------------
# Role enforcement (admin-only)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_publish_anonymous_returns_403(session_factory):
    """No cookie → 403 from require_role('admin')."""
    async with session_factory() as session:
        dep = require_role("admin")
        with pytest.raises(HTTPException) as exc:
            await dep(db=session, gw_account=None)
    assert exc.value.status_code == 403


@pytest.mark.anyio
@pytest.mark.parametrize(
    "non_admin_role",
    ["sme_reviewer", "case_manager", "dao_reviewer"],
)
async def test_publish_non_admin_role_returns_403(
    session_factory, non_admin_role
):
    """sme_reviewer / case_manager / dao_reviewer cannot publish."""
    async with session_factory() as session:
        _, cookie = await _make_account_with_roles(
            session, f"{non_admin_role}-publish@example.com", [non_admin_role]
        )
        dep = require_role("admin")
        with pytest.raises(HTTPException) as exc:
            await dep(db=session, gw_account=cookie)
    assert exc.value.status_code == 403
    assert "Insufficient" in exc.value.detail


# ---------------------------------------------------------------------------
# Cross-guard: published versions cannot be reviewed (T23.2 invariant)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_review_after_publish_returns_409(session_factory):
    """Once published, record_review path is closed (re-assertion)."""
    async with session_factory() as session:
        _, _, _, vid = await _seed_approved_version(session, "voc-lock")
        _, cookie = await _make_account_with_roles(
            session, "admin-lock@example.com", ["admin"]
        )
        account = await _resolve_admin_account(session, cookie)
        await assessments_review.publish_version_endpoint(
            version_id=vid, db=session, account=account,
        )
        # Now try to submit a review — must 409.
        _, rev_cookie = await _make_account_with_roles(
            session, "rev-lock@example.com", ["sme_reviewer"]
        )
        rev_account = await any_of_roles(
            "case_manager", "sme_reviewer", "dao_reviewer"
        )(db=session, gw_account=rev_cookie)
        body = assessments_review.ReviewBody(
            action="approve", comment="too late"
        )
        with pytest.raises(HTTPException) as exc:
            await assessments_review.submit_review(
                version_id=vid, body=body, db=session, account=rev_account,
            )
    assert exc.value.status_code == 409
