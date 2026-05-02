"""Tests for the Haiku-augmented plan endpoints."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.integrations.llm import _cache
from app.main import app

_VALID_UUID = "00000000-0000-4000-8000-000000000aa1"
_VALIDATE_TOKEN_PATCH = "app.core.auth.validate_token"
_TOKEN_EXISTS_PATCH = "app.core.auth.token_exists"
_GET_SESSION_PATCH = "app.routes.plan_haiku.get_session_by_id"
_EXPLAIN_PATCH = "app.routes.plan_haiku.explain_match"
_COMPOSE_PATCH = "app.routes.plan_haiku.compose_next_steps"


@pytest.fixture(autouse=True)
def _clear_caches() -> None:
    _cache.match_explanation_cache.clear()
    _cache.next_step_cache.clear()


@pytest.fixture(autouse=True)
def _mock_token_validation():
    """Mock auth so request reaches the handler."""
    async def _validate(db, token):
        if token.startswith("test-token-"):
            return token.removeprefix("test-token-")
        return None

    async def _exists(db, token):
        return False

    with (
        patch(_VALIDATE_TOKEN_PATCH, side_effect=_validate),
        patch(_TOKEN_EXISTS_PATCH, side_effect=_exists),
    ):
        yield


def _make_row(*, with_match: bool = True, with_steps: bool = True) -> dict:
    plan = {
        "plan_id": "p1",
        "strong_matches": [
            {
                "title": "CNA",
                "company": "TX Health",
                "url": "https://example.com/cna",
                "location": "Fort Worth, TX",
                "score_breakdown": {
                    "skills": 0.5, "title_family": 0.7, "industry": 0.6,
                    "years": 0.3, "education": 0.2, "certifications": 0.4,
                    "industry_aligned": True,
                },
            },
        ] if with_match else [],
        "possible_matches": [],
        "after_repair": [],
        "immediate_next_steps": [
            "Visit Workforce Solutions for Tarrant County",
            "Contact Trinity Metro about a bus pass",
        ] if with_steps else [],
    }
    return {
        "id": _VALID_UUID,
        "barriers": json.dumps(["TRANSIT", "CHILDCARE"]),
        "qualifications": "Former CNA",
        "plan": json.dumps(plan),
    }


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


class TestExplainMatchRoute:
    @pytest.mark.asyncio
    async def test_returns_haiku_explanation(self) -> None:
        """Happy path: handler delegates to explain_match and returns 200."""
        fake_explain = AsyncMock(return_value={
            "text": "You match this CNA role.", "source": "haiku", "cached": False,
        })
        async def _get(_db, _sid):
            return _make_row()
        with (
            patch(_GET_SESSION_PATCH, side_effect=_get),
            patch(_EXPLAIN_PATCH, fake_explain),
        ):
            async with _client() as ac:
                resp = await ac.post(
                    f"/api/plan/{_VALID_UUID}/match/0/explain"
                    f"?token=test-token-{_VALID_UUID}",
                )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["source"] == "haiku"
        assert body["job_index"] == 0
        kwargs = fake_explain.call_args.kwargs
        assert kwargs["barriers"] == ["TRANSIT", "CHILDCARE"]
        assert kwargs["score_breakdown"]["title_family"] == 0.7

    @pytest.mark.asyncio
    async def test_404_when_session_missing(self) -> None:
        async def _get(_db, _sid):
            return None
        with patch(_GET_SESSION_PATCH, side_effect=_get):
            async with _client() as ac:
                resp = await ac.post(
                    f"/api/plan/{_VALID_UUID}/match/0/explain"
                    f"?token=test-token-{_VALID_UUID}",
                )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_400_when_no_matches(self) -> None:
        async def _get(_db, _sid):
            return _make_row(with_match=False)
        with patch(_GET_SESSION_PATCH, side_effect=_get):
            async with _client() as ac:
                resp = await ac.post(
                    f"/api/plan/{_VALID_UUID}/match/0/explain"
                    f"?token=test-token-{_VALID_UUID}",
                )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_404_when_index_out_of_range(self) -> None:
        async def _get(_db, _sid):
            return _make_row()
        with patch(_GET_SESSION_PATCH, side_effect=_get):
            async with _client() as ac:
                resp = await ac.post(
                    f"/api/plan/{_VALID_UUID}/match/5/explain"
                    f"?token=test-token-{_VALID_UUID}",
                )
        assert resp.status_code == 404


class TestComposeNextStepsRoute:
    @pytest.mark.asyncio
    async def test_compose_returns_haiku_steps(self) -> None:
        fake = AsyncMock(return_value={
            "steps": ["Step 1.", "Step 2.", "Step 3.", "Step 4."],
            "source": "haiku", "cached": False,
        })
        async def _get(_db, _sid):
            return _make_row()
        with (
            patch(_GET_SESSION_PATCH, side_effect=_get),
            patch(_COMPOSE_PATCH, fake),
        ):
            async with _client() as ac:
                resp = await ac.post(
                    f"/api/plan/{_VALID_UUID}/next-steps/compose"
                    f"?token=test-token-{_VALID_UUID}",
                )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["source"] == "haiku"
        assert len(body["steps"]) == 4
        kwargs = fake.call_args.kwargs
        assert kwargs["barriers"] == ["TRANSIT", "CHILDCARE"]
        assert kwargs["deterministic_steps"][0].startswith("Visit Workforce")

    @pytest.mark.asyncio
    async def test_compose_400_when_no_deterministic_steps(self) -> None:
        async def _get(_db, _sid):
            return _make_row(with_steps=False)
        with patch(_GET_SESSION_PATCH, side_effect=_get):
            async with _client() as ac:
                resp = await ac.post(
                    f"/api/plan/{_VALID_UUID}/next-steps/compose"
                    f"?token=test-token-{_VALID_UUID}",
                )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_compose_404_when_session_missing(self) -> None:
        async def _get(_db, _sid):
            return None
        with patch(_GET_SESSION_PATCH, side_effect=_get):
            async with _client() as ac:
                resp = await ac.post(
                    f"/api/plan/{_VALID_UUID}/next-steps/compose"
                    f"?token=test-token-{_VALID_UUID}",
                )
        assert resp.status_code == 404
