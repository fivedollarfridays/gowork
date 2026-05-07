"""Tests for the Claude-draft generation endpoint (T23.3).

Covers two surfaces:

* :mod:`app.ai.assessment_drafter` — the LLM-call layer that turns a
  natural-language ``source_prompt`` into a list of
  :class:`QuestionDraft` rows. Tested against a mocked
  ``get_llm_stream`` so no live Claude call leaves the suite.
* ``POST /api/admin/assessments/draft`` — the route that gates on
  admin-or-sme_reviewer, rate-limits to 10/hour per account, persists
  via :mod:`app.core.queries_assessments`, and returns the
  ``{assessment_id, version_id, status, question_count}`` envelope.

Mocking strategy
----------------
The drafter calls ``app.ai.llm_client.get_llm_stream`` exactly like
the existing :mod:`app.ai.client` does; tests patch that symbol so the
suite stays deterministic and ANTHROPIC_API_KEY is never required.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import queries_accounts, queries_roles
from app.core.accounts_schema import apply_ddl as apply_accounts_ddl
from app.core.assessments_schema import apply_ddl as apply_assessments_ddl
from app.core.roles_schema import apply_ddl as apply_roles_ddl
from app.routes._auth_claim_helpers import build_account_cookie_value


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def drafter_engine(test_engine):
    """``test_engine`` plus accounts + roles + assessments DDL."""
    async with test_engine.begin() as conn:
        await conn.run_sync(apply_accounts_ddl)
        await conn.run_sync(apply_roles_ddl)
        await conn.run_sync(apply_assessments_ddl)
    return test_engine


@pytest.fixture
def drafter_session_factory(drafter_engine):
    return async_sessionmaker(
        drafter_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.fixture
async def drafter_client(drafter_engine):
    """Async test client mounted on the assessments-DDL-applied engine."""
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


def _claude_response(question_count: int = 2) -> str:
    """Return a JSON envelope matching the drafter contract."""
    return json.dumps({
        "questions": [
            {
                "prompt": f"What is concept {i}?",
                "kind": "mcq",
                "rubric": f"Looking for keyword {i}",
                "scoring_weight": 1.0,
            }
            for i in range(1, question_count + 1)
        ]
    })


def _fake_stream_factory(payload: str):
    """Build an async generator returning *payload* in two chunks."""
    async def _gen(_system: str, _user: str):
        midpoint = max(1, len(payload) // 2)
        yield payload[:midpoint]
        yield payload[midpoint:]
    return _gen


async def _grant(session: AsyncSession, email: str, role: str | None) -> int:
    account_id = await queries_accounts.create_account(session, email=email)
    if role is not None:
        await queries_roles.grant_role(session, account_id, role)
    return account_id


# ---------------------------------------------------------------------------
# QuestionDraft Pydantic schema
# ---------------------------------------------------------------------------


def test_question_draft_validates_required_fields():
    """``prompt`` / ``kind`` / ``rubric`` are required; missing one raises."""
    from pydantic import ValidationError

    from app.ai.assessment_drafter import QuestionDraft

    # ``scoring_weight`` defaults to 1.0; the OTHER three are required.
    with pytest.raises(ValidationError):
        QuestionDraft(kind="mcq", rubric="r")  # type: ignore[call-arg]
    # Empty prompt also fails (min_length=1).
    with pytest.raises(ValidationError):
        QuestionDraft(prompt="", kind="mcq", rubric="r")


def test_question_draft_accepts_canonical_payload():
    """Happy: canonical payload coerces and returns a QuestionDraft."""
    from app.ai.assessment_drafter import QuestionDraft

    qd = QuestionDraft(
        prompt="What is X?",
        kind="mcq",
        rubric="Look for keyword X",
        scoring_weight=1.5,
    )
    assert qd.prompt == "What is X?"
    assert qd.kind == "mcq"
    assert qd.scoring_weight == 1.5


def test_question_draft_rejects_invalid_kind():
    """``kind`` must be one of QUESTION_KINDS — anything else is rejected."""
    from pydantic import ValidationError

    from app.ai.assessment_drafter import QuestionDraft

    with pytest.raises(ValidationError):
        QuestionDraft(
            prompt="q", kind="essay", rubric="r", scoring_weight=1.0,
        )


# ---------------------------------------------------------------------------
# draft_questions — drafter module surface
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_draft_questions_happy_path_returns_list():
    """Mocked Claude payload yields N validated QuestionDraft rows."""
    from app.ai.assessment_drafter import draft_questions

    payload = _claude_response(question_count=3)
    fake = _fake_stream_factory(payload)
    with patch("app.ai.assessment_drafter.get_llm_stream", side_effect=fake):
        drafts = await draft_questions(
            kind="skill_probe",
            track="vocational",
            source_prompt="Test forklift safety knowledge.",
            target_question_count=3,
        )
    assert len(drafts) == 3
    assert drafts[0].prompt == "What is concept 1?"
    assert all(d.kind == "mcq" for d in drafts)


@pytest.mark.anyio
async def test_draft_questions_invalid_json_raises_value_error():
    """Non-JSON Claude output bubbles up as ValueError for the route to map."""
    from app.ai.assessment_drafter import draft_questions

    fake = _fake_stream_factory("not json at all")
    with patch("app.ai.assessment_drafter.get_llm_stream", side_effect=fake):
        with pytest.raises(ValueError):
            await draft_questions(
                kind="skill_probe",
                track="vocational",
                source_prompt="prompt",
            )


@pytest.mark.anyio
async def test_draft_questions_missing_questions_key_raises():
    """JSON without a ``questions`` array is malformed."""
    from app.ai.assessment_drafter import draft_questions

    fake = _fake_stream_factory(json.dumps({"items": []}))
    with patch("app.ai.assessment_drafter.get_llm_stream", side_effect=fake):
        with pytest.raises(ValueError):
            await draft_questions(
                kind="skill_probe",
                track="vocational",
                source_prompt="prompt",
            )


# ---------------------------------------------------------------------------
# POST /api/admin/assessments/draft — happy path + persistence
# ---------------------------------------------------------------------------


def _set_cookie(client: AsyncClient, account_id: int) -> None:
    client.cookies.set("gw_account", build_account_cookie_value(account_id))


@pytest.mark.anyio
async def test_draft_endpoint_admin_happy_path(
    drafter_client, drafter_session_factory,
):
    """Admin caller -> 200 with assessment_id + version_id + status=draft."""
    async with drafter_session_factory() as session:
        account_id = await _grant(session, "admin@example.com", "admin")
    _set_cookie(drafter_client, account_id)

    payload = _claude_response(question_count=2)
    fake = _fake_stream_factory(payload)
    with patch("app.ai.assessment_drafter.get_llm_stream", side_effect=fake):
        resp = await drafter_client.post(
            "/api/admin/assessments/draft",
            json={
                "slug": "probe-happy",
                "kind": "skill_probe",
                "track": "vocational",
                "source_prompt": "Forklift basics",
            },
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "draft"
    assert body["question_count"] == 2
    assert isinstance(body["assessment_id"], int)
    assert isinstance(body["version_id"], int)


@pytest.mark.anyio
async def test_draft_endpoint_sme_reviewer_allowed(
    drafter_client, drafter_session_factory,
):
    """sme_reviewer role is also allowed (any-of-roles gate)."""
    async with drafter_session_factory() as session:
        account_id = await _grant(session, "sme@example.com", "sme_reviewer")
    _set_cookie(drafter_client, account_id)

    fake = _fake_stream_factory(_claude_response(2))
    with patch("app.ai.assessment_drafter.get_llm_stream", side_effect=fake):
        resp = await drafter_client.post(
            "/api/admin/assessments/draft",
            json={
                "slug": "probe-sme",
                "kind": "skill_probe",
                "track": "vocational",
                "source_prompt": "Test prompt",
            },
        )
    assert resp.status_code == 200, resp.text


@pytest.mark.anyio
async def test_draft_endpoint_case_manager_403(
    drafter_client, drafter_session_factory,
):
    """case_manager lacks both required roles -> 403."""
    async with drafter_session_factory() as session:
        account_id = await _grant(session, "cm@example.com", "case_manager")
    _set_cookie(drafter_client, account_id)

    resp = await drafter_client.post(
        "/api/admin/assessments/draft",
        json={
            "slug": "probe-cm",
            "kind": "skill_probe",
            "track": "vocational",
            "source_prompt": "x",
        },
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_draft_endpoint_anonymous_403(drafter_client):
    """No cookie -> 403 (anonymous-first invariant for admin routes)."""
    resp = await drafter_client.post(
        "/api/admin/assessments/draft",
        json={
            "slug": "probe-anon",
            "kind": "skill_probe",
            "track": "vocational",
            "source_prompt": "x",
        },
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Malformed Claude response & rate limiting
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_draft_endpoint_malformed_claude_returns_502(
    drafter_client, drafter_session_factory,
):
    """Bad JSON from the LLM -> 502 with a sanitized error body."""
    async with drafter_session_factory() as session:
        account_id = await _grant(session, "admin2@example.com", "admin")
    _set_cookie(drafter_client, account_id)

    fake = _fake_stream_factory("garbage non-json")
    with patch("app.ai.assessment_drafter.get_llm_stream", side_effect=fake):
        resp = await drafter_client.post(
            "/api/admin/assessments/draft",
            json={
                "slug": "probe-bad",
                "kind": "skill_probe",
                "track": "vocational",
                "source_prompt": "x",
            },
        )
    assert resp.status_code == 502
    detail = resp.json().get("detail", "")
    # Sanitized: must not leak the raw Claude bytes.
    assert "garbage non-json" not in detail


@pytest.mark.anyio
async def test_draft_endpoint_rate_limit_caps_at_ten_per_hour(
    drafter_client, drafter_session_factory,
):
    """11th call within the hour -> 429."""
    async with drafter_session_factory() as session:
        account_id = await _grant(session, "admin3@example.com", "admin")
    _set_cookie(drafter_client, account_id)

    fake = _fake_stream_factory(_claude_response(1))
    with patch("app.ai.assessment_drafter.get_llm_stream", side_effect=fake):
        for i in range(10):
            resp = await drafter_client.post(
                "/api/admin/assessments/draft",
                json={
                    "slug": f"probe-rl-{i}",
                    "kind": "skill_probe",
                    "track": "vocational",
                    "source_prompt": "x",
                },
            )
            assert resp.status_code == 200, f"call {i}: {resp.text}"
        resp = await drafter_client.post(
            "/api/admin/assessments/draft",
            json={
                "slug": "probe-rl-11",
                "kind": "skill_probe",
                "track": "vocational",
                "source_prompt": "x",
            },
        )
    assert resp.status_code == 429


# ---------------------------------------------------------------------------
# any_of_roles helper — direct unit coverage so T23.4 can rely on it
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_any_of_roles_allows_first_match(drafter_session_factory):
    """The dependency returns when any one of the supplied roles is held."""
    from app.core.auth_roles import any_of_roles

    async with drafter_session_factory() as session:
        account_id = await _grant(session, "any1@example.com", "sme_reviewer")
        cookie = build_account_cookie_value(account_id)
        dep = any_of_roles("admin", "sme_reviewer")
        result = await dep(db=session, gw_account=cookie)
        assert result["id"] == account_id


@pytest.mark.anyio
async def test_any_of_roles_403_when_none_held(drafter_session_factory):
    """No matching role -> HTTPException 403."""
    from fastapi import HTTPException

    from app.core.auth_roles import any_of_roles

    async with drafter_session_factory() as session:
        account_id = await _grant(session, "any2@example.com", "case_manager")
        cookie = build_account_cookie_value(account_id)
        dep = any_of_roles("admin", "sme_reviewer")
        with pytest.raises(HTTPException) as exc:
            await dep(db=session, gw_account=cookie)
        assert exc.value.status_code == 403
