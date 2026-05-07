"""End-to-end smoke for the Sprint 23 assessment authoring chain (T23.10).

Drives the full draft → review-approve → publish → public-fetch path
through the actual route handlers via :class:`httpx.AsyncClient` over
:class:`httpx.ASGITransport`. The Claude call inside
``assessments_admin.draft`` is mocked at the ``get_llm_stream`` boundary
so the suite stays deterministic and ANTHROPIC_API_KEY is never required.

This test is the **integration gate** for Sprint 23. If any of the four
endpoints (admin draft, reviewer queue, publish, public fetch) regress
the contract — payload shape, status transition, role gating, anonymous
access for the public route, or the load-bearing provenance invariant —
this test breaks.

Charter invariant verified
--------------------------
After publish, the published row has all four provenance columns
non-null: ``drafted_by`` (admin id), ``reviewed_by`` (sme id),
``approved_by`` (admin id again — narrower publish authority),
``published_at`` (utcnow ISO timestamp).
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import queries_accounts, queries_roles
from app.core.accounts_schema import apply_ddl as apply_accounts_ddl
from app.core.assessments_schema import apply_ddl as apply_assessments_ddl
from app.core.roles_schema import apply_ddl as apply_roles_ddl
from app.routes._auth_claim_helpers import (
    SESSION_COOKIE_NAME,
    build_account_cookie_value,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def e2e_engine(test_engine):
    """``test_engine`` plus accounts + roles + assessments DDL."""
    async with test_engine.begin() as conn:
        await conn.run_sync(apply_accounts_ddl)
        await conn.run_sync(apply_roles_ddl)
        await conn.run_sync(apply_assessments_ddl)
    return test_engine


@pytest.fixture
def e2e_session_factory(e2e_engine):
    return async_sessionmaker(
        e2e_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.fixture
async def e2e_client(e2e_engine):
    """AsyncClient mounted on the app with the e2e engine wired in."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def _reset_drafter_rate_limiter():
    """Ensure each test gets a fresh rate-limit bucket."""
    from app.routes import assessments_admin

    assessments_admin._account_limiter.clear()
    yield
    assessments_admin._account_limiter.clear()


def _claude_response_for(slug: str, count: int = 3) -> str:
    """Deterministic Claude-shaped JSON for *count* questions."""
    return json.dumps({
        "questions": [
            {
                "prompt": f"[{slug}] Question {i}: what is concept {i}?",
                "kind": "mcq",
                "rubric": f"[{slug}] rubric for question {i}",
                "scoring_weight": 1.0,
            }
            for i in range(1, count + 1)
        ]
    })


def _fake_stream_factory(payload: str):
    async def _gen(_system: str, _user: str):
        yield payload
    return _gen


# ---------------------------------------------------------------------------
# E2E — full chain
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_e2e_draft_review_publish_public_fetch_chain(
    e2e_client, e2e_session_factory
):
    """Full chain: admin drafts → sme approves → admin publishes → fetch."""
    slug = "e2e-cdl-knowledge"

    # ------ Set up accounts + roles + cookies ------
    async with e2e_session_factory() as session:
        admin_id = await queries_accounts.create_account(
            session, email="e2e-admin@example.com"
        )
        await queries_roles.grant_role(session, admin_id, "admin")

        sme_id = await queries_accounts.create_account(
            session, email="e2e-sme@example.com"
        )
        await queries_roles.grant_role(session, sme_id, "sme_reviewer")

    admin_cookie = build_account_cookie_value(admin_id)
    sme_cookie = build_account_cookie_value(sme_id)

    # ------ STEP 1: admin drafts (Claude mocked at boundary) ------
    payload = _claude_response_for(slug, count=3)
    with patch(
        "app.ai.assessment_drafter.get_llm_stream",
        side_effect=_fake_stream_factory(payload),
    ):
        draft_resp = await e2e_client.post(
            "/api/admin/assessments/draft",
            json={
                "slug": slug,
                "kind": "skill_probe",
                "track": "vocational",
                "source_prompt": "Test forklift safety knowledge.",
            },
            cookies={SESSION_COOKIE_NAME: admin_cookie},
        )
    assert draft_resp.status_code == 200, draft_resp.text
    draft_body = draft_resp.json()
    assessment_id = draft_body["assessment_id"]
    version_id = draft_body["version_id"]
    assert draft_body["status"] == "draft"
    assert draft_body["question_count"] == 3

    # ------ STEP 2: sme_reviewer approves ------
    review_resp = await e2e_client.post(
        f"/api/admin/assessments/{version_id}/review",
        json={"action": "approve", "comment": "Looks good for pilot."},
        cookies={SESSION_COOKIE_NAME: sme_cookie},
    )
    assert review_resp.status_code == 200, review_resp.text

    # ------ STEP 3: admin publishes ------
    publish_resp = await e2e_client.post(
        f"/api/admin/assessments/{version_id}/publish",
        cookies={SESSION_COOKIE_NAME: admin_cookie},
    )
    assert publish_resp.status_code == 200, publish_resp.text
    publish_body = publish_resp.json()
    assert publish_body["assessment_id"] == assessment_id
    assert publish_body["version_id"] == version_id
    assert publish_body["slug"] == slug
    assert publish_body["public_url"] == f"/api/assessments/{slug}"
    assert publish_body["published_at"] is not None

    # ------ STEP 4a: anonymous fetch the public version ------
    anon_resp = await e2e_client.get(f"/api/assessments/{slug}")
    assert anon_resp.status_code == 200, anon_resp.text
    anon_body = anon_resp.json()
    assert anon_body["slug"] == slug
    assert anon_body["kind"] == "skill_probe"
    assert anon_body["track"] == "vocational"
    assert len(anon_body["questions"]) == 3
    # Charter invariant: rubric_json never leaks publicly.
    for q in anon_body["questions"]:
        assert "rubric_json" not in q
        assert "rubric" not in q
    assert anon_resp.headers.get("cache-control") == "public, max-age=60"

    # ------ STEP 4b: claimed fetch the same — equivalent payload ------
    claimed_resp = await e2e_client.get(
        f"/api/assessments/{slug}",
        cookies={SESSION_COOKIE_NAME: admin_cookie},
    )
    assert claimed_resp.status_code == 200
    assert claimed_resp.json() == anon_body, (
        "anonymous-first invariant: anonymous + claimed sessions must "
        "see byte-equivalent public assessment payloads"
    )

    # ------ STEP 5: provenance assertion ------
    # All four columns non-null on the published row — the load-bearing
    # charter invariant for assessment publication.
    async with e2e_session_factory() as session:
        row = (await session.execute(
            text(
                "SELECT drafted_by, reviewed_by, approved_by, published_at, "
                "       status "
                "FROM assessment_versions WHERE id = :vid"
            ),
            {"vid": version_id},
        )).mappings().first()
    assert row is not None
    assert row["status"] == "published"
    assert row["drafted_by"] == admin_id, "drafted_by must be the drafter"
    assert row["reviewed_by"] == sme_id, "reviewed_by must be the approver"
    assert row["approved_by"] == admin_id, "approved_by populated by publish"
    assert row["published_at"] is not None, "published_at must be set"


@pytest.mark.anyio
async def test_e2e_draft_unpublished_returns_404(
    e2e_client, e2e_session_factory
):
    """Drafted-but-not-published versions are not publicly fetchable."""
    slug = "e2e-not-published"

    async with e2e_session_factory() as session:
        admin_id = await queries_accounts.create_account(
            session, email="e2e-draft-only@example.com"
        )
        await queries_roles.grant_role(session, admin_id, "admin")
    admin_cookie = build_account_cookie_value(admin_id)

    payload = _claude_response_for(slug, count=2)
    with patch(
        "app.ai.assessment_drafter.get_llm_stream",
        side_effect=_fake_stream_factory(payload),
    ):
        await e2e_client.post(
            "/api/admin/assessments/draft",
            json={
                "slug": slug,
                "kind": "knowledge_check",
                "track": "generic",
                "source_prompt": "Generic knowledge check.",
            },
            cookies={SESSION_COOKIE_NAME: admin_cookie},
        )

    # No approve, no publish — public fetch must 404.
    resp = await e2e_client.get(f"/api/assessments/{slug}")
    assert resp.status_code == 404
