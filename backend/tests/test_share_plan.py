"""Tests for plan sharing — POST /api/plan/{session_id}/share, GET /api/plan/shared/{token}."""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _seed_session_with_plan(
    test_engine, session_id: str, *, auth_token: str = "share-auth-tok",
) -> str:
    """Insert a session + feedback token. Return the auth token."""
    factory = get_async_session_factory()
    async with factory() as db:
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(days=30)).isoformat()
        plan = json.dumps({
            "plan_id": "test", "session_id": session_id,
            "barriers": [], "immediate_next_steps": ["Visit career center"],
        })
        await db.execute(
            text(
                "INSERT INTO sessions (id, created_at, barriers, plan, expires_at) "
                "VALUES (:id, :ts, :b, :p, :exp)"
            ),
            {"id": session_id, "ts": now.isoformat(), "b": "[]", "p": plan, "exp": expires},
        )
        await db.execute(
            text(
                "INSERT INTO feedback_tokens (token, session_id, created_at, expires_at) "
                "VALUES (:tok, :sid, :ts, :exp)"
            ),
            {"tok": auth_token, "sid": session_id, "ts": now.isoformat(), "exp": expires},
        )
        await db.commit()
    return auth_token


# ---------------------------------------------------------------------------
# Tests: POST /api/plan/{session_id}/share
# ---------------------------------------------------------------------------

class TestCreateShareToken:
    """POST /api/plan/{session_id}/share — generate a shareable link."""

    @pytest.mark.anyio
    async def test_creates_token_and_url(self, client, test_engine):
        sid = "00000000-0000-4000-8000-share0000001"
        tok = await _seed_session_with_plan(test_engine, sid, auth_token="auth-share-1")

        resp = await client.post(f"/api/plan/{sid}/share?token={tok}")
        assert resp.status_code == 200
        data = resp.json()
        assert "share_token" in data
        assert "url" in data
        assert len(data["share_token"]) > 8
        assert data["share_token"] in data["url"]

    @pytest.mark.anyio
    async def test_no_plan_returns_400(self, client, test_engine):
        sid = "00000000-0000-4000-8000-share0000002"
        factory = get_async_session_factory()
        async with factory() as db:
            now = datetime.now(timezone.utc)
            expires = (now + timedelta(days=30)).isoformat()
            await db.execute(
                text(
                    "INSERT INTO sessions (id, created_at, barriers, plan, expires_at) "
                    "VALUES (:id, :ts, :b, :p, :exp)"
                ),
                {"id": sid, "ts": now.isoformat(), "b": "[]", "p": None, "exp": expires},
            )
            await db.execute(
                text(
                    "INSERT INTO feedback_tokens (token, session_id, created_at, expires_at) "
                    "VALUES (:tok, :sid, :ts, :exp)"
                ),
                {"tok": "auth-share-2", "sid": sid, "ts": now.isoformat(), "exp": expires},
            )
            await db.commit()

        resp = await client.post(f"/api/plan/{sid}/share?token=auth-share-2")
        assert resp.status_code == 400

    @pytest.mark.anyio
    async def test_invalid_token_returns_401(self, client, test_engine):
        resp = await client.post(
            "/api/plan/00000000-0000-4000-8000-share0000003/share?token=bogus"
        )
        assert resp.status_code == 401

    @pytest.mark.anyio
    async def test_unique_tokens_per_call(self, client, test_engine):
        sid = "00000000-0000-4000-8000-share0000004"
        tok = await _seed_session_with_plan(test_engine, sid, auth_token="auth-share-4")

        r1 = await client.post(f"/api/plan/{sid}/share?token={tok}")
        r2 = await client.post(f"/api/plan/{sid}/share?token={tok}")
        assert r1.json()["share_token"] != r2.json()["share_token"]


# ---------------------------------------------------------------------------
# Tests: GET /api/plan/shared/{token}
# ---------------------------------------------------------------------------

class TestGetSharedPlan:
    """GET /api/plan/shared/{token} — public plan retrieval."""

    @pytest.mark.anyio
    async def test_returns_plan_data(self, client, test_engine):
        sid = "00000000-0000-4000-8000-share0000005"
        tok = await _seed_session_with_plan(test_engine, sid, auth_token="auth-share-5")

        r1 = await client.post(f"/api/plan/{sid}/share?token={tok}")
        share_tok = r1.json()["share_token"]

        r2 = await client.get(f"/api/plan/shared/{share_tok}")
        assert r2.status_code == 200
        data = r2.json()
        assert data["session_id"] == sid
        assert "barriers" in data
        assert "next_steps" in data

    @pytest.mark.anyio
    async def test_unknown_token_returns_404(self, client, test_engine):
        resp = await client.get("/api/plan/shared/nonexistent-token-xyz")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_expired_token_returns_410(self, client, test_engine):
        sid = "00000000-0000-4000-8000-share0000006"
        tok = await _seed_session_with_plan(test_engine, sid, auth_token="auth-share-6")

        r1 = await client.post(f"/api/plan/{sid}/share?token={tok}")
        share_tok = r1.json()["share_token"]

        # Expire the share token
        factory = get_async_session_factory()
        async with factory() as db:
            past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            await db.execute(
                text("UPDATE share_tokens SET expires_at = :exp WHERE token = :tok"),
                {"exp": past, "tok": share_tok},
            )
            await db.commit()

        r2 = await client.get(f"/api/plan/shared/{share_tok}")
        assert r2.status_code == 410
