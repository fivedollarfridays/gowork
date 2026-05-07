"""Route tests for the public assessment-fetch endpoint (T23.6).

Covers ``GET /api/assessments/{slug}`` end-to-end against the real DB
layer. The route is fully public (no auth dependency) and serves the
candidate-facing payload — published versions only, ``rubric_json``
stripped from each question, ``Cache-Control: public, max-age=60``.

Behaviours covered
------------------

* published-200: a slug with a published version returns the full
  public payload (slug, kind, track, version_number, published_at,
  questions[]).
* draft-only-404: a slug whose only version is in draft (never
  approved) returns 404 — drafts are never publicly fetchable.
* approved-but-not-published-404: a version stuck in ``approved`` is
  also 404 — the public surface is gated strictly on
  ``status='published'``.
* rubric-not-leaked: a version whose questions carry ``rubric_json``
  must NOT surface that field in the public response, even after the
  version is published.
* cache-header: the ``Cache-Control: public, max-age=60`` header is
  set on a 200 response.
* anon-vs-claimed-equivalence: an anonymous client and an account-
  cookie'd client get byte-equivalent payloads + status codes (the
  anonymous-first invariant for this route — the route doesn't take a
  ``session_id`` so the auto-discovery test won't pick it up; this
  smoke is the explicit guard).
* unknown-slug-404: a slug that doesn't exist at all (no row in
  ``assessments``) returns 404, same as draft-only.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import queries_accounts, queries_assessments, queries_roles
from app.core.accounts_schema import apply_ddl as apply_accounts_ddl
from app.core.assessments_schema import apply_ddl as apply_assessments_ddl
from app.core.roles_schema import apply_ddl as apply_roles_ddl
from app.routes import assessments_public
from app.routes._auth_claim_helpers import build_account_cookie_value


# ---------------------------------------------------------------------------
# Engine + fixture stack (mirrors test_assessments_publish.py)
# ---------------------------------------------------------------------------


@pytest.fixture
async def public_engine(db_engine):
    """``db_engine`` plus accounts + roles + assessments DDL applied."""
    async with db_engine.begin() as conn:
        await conn.run_sync(apply_accounts_ddl)
        await conn.run_sync(apply_roles_ddl)
        await conn.run_sync(apply_assessments_ddl)
    return db_engine


@pytest.fixture
def session_factory(public_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        public_engine, class_=AsyncSession, expire_on_commit=False
    )


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------


async def _seed_published_version(
    session: AsyncSession, slug: str, *, rubric: str = '{"answer": "x"}'
) -> tuple[int, int]:
    """Create + draft + approve + publish a version for *slug*.

    Returns ``(assessment_id, version_id)`` on a row whose status is
    now ``published`` and whose questions carry ``rubric_json``.
    """
    author_id = await queries_accounts.create_account(
        session, email=f"{slug}-author@example.com"
    )
    reviewer_id = await queries_accounts.create_account(
        session, email=f"{slug}-reviewer@example.com"
    )
    admin_id = await queries_accounts.create_account(
        session, email=f"{slug}-admin@example.com"
    )
    aid = await queries_assessments.create_assessment(
        session, slug=slug, kind="skill_probe",
        track="vocational", created_by=author_id,
    )
    vid = await queries_assessments.create_draft_version(
        session, assessment_id=aid, drafted_by=author_id,
        questions=[
            {
                "position": 1, "prompt": "What is 2+2?", "kind": "mcq",
                "rubric_json": rubric, "scoring_weight": 1.0,
            },
            {
                "position": 2, "prompt": "Describe a workday.",
                "kind": "freeform",
                "rubric_json": '{"keywords": ["team", "schedule"]}',
                "scoring_weight": 2.5,
            },
        ],
    )
    await queries_assessments.record_review(
        session, version_id=vid, reviewer_id=reviewer_id,
        action="approve", comment="ok",
    )
    await queries_assessments.publish_version(
        session, version_id=vid, approved_by=admin_id,
    )
    return aid, vid


async def _seed_draft_only(
    session: AsyncSession, slug: str
) -> int:
    """Seed a slug whose only version is a draft (never approved)."""
    author_id = await queries_accounts.create_account(
        session, email=f"{slug}-author@example.com"
    )
    aid = await queries_assessments.create_assessment(
        session, slug=slug, kind="skill_probe",
        track="vocational", created_by=author_id,
    )
    await queries_assessments.create_draft_version(
        session, assessment_id=aid, drafted_by=author_id,
        questions=[{
            "position": 1, "prompt": "p1", "kind": "mcq",
            "rubric_json": '{"a": 1}', "scoring_weight": 1.0,
        }],
    )
    return aid


async def _seed_approved_only(
    session: AsyncSession, slug: str
) -> int:
    """Seed a slug whose latest version is approved but NOT published."""
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
            "rubric_json": '{"a": 1}', "scoring_weight": 1.0,
        }],
    )
    await queries_assessments.record_review(
        session, version_id=vid, reviewer_id=reviewer_id,
        action="approve", comment="ok",
    )
    return aid


# ---------------------------------------------------------------------------
# Direct-call tests (exercise the route function with a real session)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_published_returns_full_public_payload(session_factory):
    """A published slug returns slug/kind/track/version_number/questions."""
    async with session_factory() as session:
        await _seed_published_version(session, "voc-pub")
        from fastapi import Response
        resp = Response()
        result = await assessments_public.get_published_assessment(
            slug="voc-pub", response=resp, db=session,
        )
    assert result["slug"] == "voc-pub"
    assert result["kind"] == "skill_probe"
    assert result["track"] == "vocational"
    assert result["version_number"] == 1
    assert result["published_at"] is not None
    assert len(result["questions"]) == 2
    assert result["questions"][0]["position"] == 1
    assert result["questions"][0]["prompt"] == "What is 2+2?"
    assert result["questions"][0]["kind"] == "mcq"
    assert result["questions"][0]["scoring_weight"] == 1.0


@pytest.mark.anyio
async def test_published_response_strips_rubric_json(session_factory):
    """rubric_json MUST NOT appear in any public question payload."""
    async with session_factory() as session:
        await _seed_published_version(
            session, "voc-secret",
            rubric='{"correct": "this-must-not-leak"}',
        )
        from fastapi import Response
        resp = Response()
        result = await assessments_public.get_published_assessment(
            slug="voc-secret", response=resp, db=session,
        )
    for q in result["questions"]:
        assert "rubric_json" not in q, (
            f"rubric_json leaked in public payload: {q!r}"
        )
    # Belt-and-suspenders: the secret string must not surface anywhere.
    assert "this-must-not-leak" not in repr(result)


@pytest.mark.anyio
async def test_draft_only_slug_returns_404(session_factory):
    """A slug whose only version is a draft → 404 (not publicly fetchable)."""
    async with session_factory() as session:
        await _seed_draft_only(session, "voc-draft")
        from fastapi import Response
        resp = Response()
        with pytest.raises(HTTPException) as exc:
            await assessments_public.get_published_assessment(
                slug="voc-draft", response=resp, db=session,
            )
    assert exc.value.status_code == 404


@pytest.mark.anyio
async def test_approved_but_not_published_returns_404(session_factory):
    """A slug stuck in ``approved`` (no publish call yet) → 404."""
    async with session_factory() as session:
        await _seed_approved_only(session, "voc-appr")
        from fastapi import Response
        resp = Response()
        with pytest.raises(HTTPException) as exc:
            await assessments_public.get_published_assessment(
                slug="voc-appr", response=resp, db=session,
            )
    assert exc.value.status_code == 404


@pytest.mark.anyio
async def test_unknown_slug_returns_404(session_factory):
    """A slug with no assessment row at all → 404."""
    async with session_factory() as session:
        from fastapi import Response
        resp = Response()
        with pytest.raises(HTTPException) as exc:
            await assessments_public.get_published_assessment(
                slug="nope-nope-nope", response=resp, db=session,
            )
    assert exc.value.status_code == 404


@pytest.mark.anyio
async def test_published_sets_cache_control_header(session_factory):
    """Successful 200 response sets ``Cache-Control: public, max-age=60``."""
    async with session_factory() as session:
        await _seed_published_version(session, "voc-cache")
        from fastapi import Response
        resp = Response()
        await assessments_public.get_published_assessment(
            slug="voc-cache", response=resp, db=session,
        )
    assert resp.headers.get("Cache-Control") == "public, max-age=60"


# ---------------------------------------------------------------------------
# Anonymous-first invariant smoke (HTTP-level, anon vs claimed cookie)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_anon_and_claimed_clients_get_equivalent_response(
    session_factory,
):
    """The route is fully public — anon and account-cookie clients match.

    Mirrors ``test_anonymous_first_invariant.py`` for a route the
    auto-discovery loop can't reach (no ``session_id`` parameter).
    The fetch endpoint MUST behave identically whether the caller
    sends no auth at all or a valid account cookie.
    """
    async with session_factory() as session:
        await _seed_published_version(session, "voc-anon")
        account_id = await queries_accounts.create_account(
            session, email="some-claimed@example.com"
        )
        # Grant a role too — exercises the case where the caller is a
        # fully-fledged claimed account, not just a no-op cookie.
        await queries_roles.grant_role(session, account_id, "admin")
        cookie = build_account_cookie_value(account_id)

    # Wire the dependency override + run the actual HTTP layer.
    from app.core.database import get_db
    from app.main import app

    async def _override_get_db():
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = _override_get_db
    try:
        client = TestClient(app, raise_server_exceptions=False)
        anon = client.get("/api/assessments/voc-anon")
        claimed = client.get(
            "/api/assessments/voc-anon",
            cookies={"gw_account": cookie},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert anon.status_code == 200
    assert claimed.status_code == 200
    assert anon.status_code == claimed.status_code
    assert anon.json() == claimed.json()
    assert (
        anon.headers.get("Cache-Control")
        == claimed.headers.get("Cache-Control")
        == "public, max-age=60"
    )


# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------


def test_assessments_public_router_registered():
    """The new router MUST be in ``app.routes.all_routers``."""
    from app.routes import all_routers
    assert assessments_public.router in all_routers, (
        "assessments_public.router not registered in "
        "app.routes.all_routers — public fetch endpoint will 404."
    )
