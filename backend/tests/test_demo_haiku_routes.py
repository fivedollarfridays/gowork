"""Tests for /api/demo/personas, /api/demo/walkthrough, /health/demo."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


class TestListPersonas:
    @pytest.mark.asyncio
    async def test_returns_five_canonical_personas(self) -> None:
        async with _client() as ac:
            resp = await ac.get("/api/demo/personas")
        assert resp.status_code == 200
        body = resp.json()
        ids = set(body["personas"].keys())
        assert {"carlos", "nurse", "forklift", "welder", "csr"}.issubset(ids)
        assert body["count"] >= 5

    @pytest.mark.asyncio
    async def test_each_persona_has_summary_and_barriers(self) -> None:
        async with _client() as ac:
            resp = await ac.get("/api/demo/personas")
        body = resp.json()
        for pid, data in body["personas"].items():
            assert data["summary"]
            assert isinstance(data["primary_barriers"], list)


class TestWalkthrough:
    @pytest.mark.asyncio
    async def test_carlos_walkthrough_returns_full_payload(self) -> None:
        async with _client() as ac:
            resp = await ac.get("/api/demo/walkthrough?persona=carlos")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        # Required sections
        for key in ("persona", "top_match", "confidence",
                    "resource_recommendations", "haiku_explanation_preview",
                    "next_steps", "data_sources"):
            assert key in body, f"missing {key}"
        # Carlos should have the criminal_record-driven Cornerstone resource
        names = [r["name"] for r in body["resource_recommendations"]]
        assert any("Cornerstone" in n for n in names), names

    @pytest.mark.asyncio
    async def test_nurse_walkthrough_high_confidence(self) -> None:
        async with _client() as ac:
            resp = await ac.get("/api/demo/walkthrough?persona=nurse")
        assert resp.status_code == 200
        body = resp.json()
        assert body["confidence"]["tier"] == "high"
        assert body["top_match"]["score_breakdown"]["industry"] == 1.00

    @pytest.mark.asyncio
    async def test_unknown_persona_404s(self) -> None:
        async with _client() as ac:
            resp = await ac.get("/api/demo/walkthrough?persona=unknown")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_default_persona_is_carlos(self) -> None:
        async with _client() as ac:
            resp = await ac.get("/api/demo/walkthrough")
        assert resp.status_code == 200
        assert resp.json()["persona"]["id"] == "carlos"


class TestHealthDemo:
    @pytest.mark.asyncio
    async def test_returns_200_with_status_and_issues(self) -> None:
        async with _client() as ac:
            resp = await ac.get("/health/demo")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] in {"green", "yellow"}
        assert isinstance(body["issues"], list)
        assert "data_sources" in body
        assert "llm" in body
        assert "personas" in body
        assert body["personas"]["count"] >= 5
