"""Tests for plan sharing — POST /api/plan/{session_id}/share, GET /api/plan/shared/{token}."""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory
from app.routes.share import _rate_limiter


@pytest.fixture(autouse=True)
def _clear_share_rate_limiter():
    """Clear the share route rate limiter between tests."""
    _rate_limiter.clear()
    yield
    _rate_limiter.clear()


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


# ---------------------------------------------------------------------------
# Tests: Edge cases + share count tracking
# ---------------------------------------------------------------------------

class TestShareEdgeCases:
    """Edge cases for share plan endpoints."""

    @pytest.mark.anyio
    async def test_share_token_is_url_safe(self, client, test_engine):
        """Tokens must not contain chars that break URLs ('+', '/', '=')."""
        sid = "00000000-0000-4000-8000-share0000007"
        tok = await _seed_session_with_plan(test_engine, sid, auth_token="auth-share-7")

        resp = await client.post(f"/api/plan/{sid}/share?token={tok}")
        share_token = resp.json()["share_token"]
        # URL-safe base64 uses only alphanumerics, -, _
        for char in share_token:
            assert char.isalnum() or char in ("-", "_"), (
                f"Token contains non-URL-safe char: {char!r}"
            )

    @pytest.mark.anyio
    async def test_session_not_found_returns_404(self, client, test_engine):
        """Sharing a non-existent session returns 404 (after auth check)."""
        # Auth will fail first with 401 since session doesn't exist
        resp = await client.post(
            "/api/plan/00000000-0000-4000-8000-share0000099/share?token=badtok"
        )
        assert resp.status_code in (401, 404)

    @pytest.mark.anyio
    async def test_duplicate_share_creates_new_tokens(self, client, test_engine):
        """Multiple shares of the same session create distinct tokens."""
        sid = "00000000-0000-4000-8000-share0000008"
        tok = await _seed_session_with_plan(test_engine, sid, auth_token="auth-share-8")

        tokens = set()
        for _ in range(3):
            resp = await client.post(f"/api/plan/{sid}/share?token={tok}")
            assert resp.status_code == 200
            tokens.add(resp.json()["share_token"])
        assert len(tokens) == 3

    @pytest.mark.anyio
    async def test_shared_plan_includes_next_steps(self, client, test_engine):
        """Shared plan response includes next_steps from plan data."""
        sid = "00000000-0000-4000-8000-share0000009"
        tok = await _seed_session_with_plan(test_engine, sid, auth_token="auth-share-9")

        r1 = await client.post(f"/api/plan/{sid}/share?token={tok}")
        share_tok = r1.json()["share_token"]

        r2 = await client.get(f"/api/plan/shared/{share_tok}")
        data = r2.json()
        assert "next_steps" in data
        assert isinstance(data["next_steps"], list)
        assert "Visit career center" in data["next_steps"]

    @pytest.mark.anyio
    async def test_shared_plan_includes_career_center(self, client, test_engine):
        """Shared plan returns career_center_name from city config."""
        sid = "00000000-0000-4000-8000-share000000a"
        tok = await _seed_session_with_plan(test_engine, sid, auth_token="auth-share-a")

        r1 = await client.post(f"/api/plan/{sid}/share?token={tok}")
        share_tok = r1.json()["share_token"]

        r2 = await client.get(f"/api/plan/shared/{share_tok}")
        data = r2.json()
        assert "career_center_name" in data
        assert len(data["career_center_name"]) > 0

    @pytest.mark.anyio
    async def test_share_plan_with_barriers(self, client, test_engine):
        """Shared plan response contains barrier list from the session."""
        sid = "00000000-0000-4000-8000-share000000b"
        factory = get_async_session_factory()
        async with factory() as db:
            now = datetime.now(timezone.utc)
            expires = (now + timedelta(days=30)).isoformat()
            plan = json.dumps({
                "plan_id": "test", "session_id": sid,
                "barriers": [], "immediate_next_steps": ["Step 1"],
            })
            barriers = json.dumps(["credit", "transportation"])
            await db.execute(
                text(
                    "INSERT INTO sessions (id, created_at, barriers, plan, expires_at) "
                    "VALUES (:id, :ts, :b, :p, :exp)"
                ),
                {"id": sid, "ts": now.isoformat(), "b": barriers, "p": plan, "exp": expires},
            )
            await db.execute(
                text(
                    "INSERT INTO feedback_tokens (token, session_id, created_at, expires_at) "
                    "VALUES (:tok, :sid, :ts, :exp)"
                ),
                {"tok": "auth-share-b", "sid": sid, "ts": now.isoformat(), "exp": expires},
            )
            await db.commit()

        r1 = await client.post(f"/api/plan/{sid}/share?token=auth-share-b")
        share_tok = r1.json()["share_token"]

        r2 = await client.get(f"/api/plan/shared/{share_tok}")
        data = r2.json()
        assert data["barriers"] == ["credit", "transportation"]

    @pytest.mark.anyio
    async def test_next_steps_truncated_at_10(self, client, test_engine):
        """_extract_next_steps returns at most 10 items."""
        sid = "00000000-0000-4000-8000-share000000c"
        factory = get_async_session_factory()
        async with factory() as db:
            now = datetime.now(timezone.utc)
            expires = (now + timedelta(days=30)).isoformat()
            plan = json.dumps({
                "plan_id": "test", "session_id": sid,
                "barriers": [],
                "immediate_next_steps": [f"Step {i}" for i in range(15)],
            })
            await db.execute(
                text(
                    "INSERT INTO sessions (id, created_at, barriers, plan, expires_at) "
                    "VALUES (:id, :ts, :b, :p, :exp)"
                ),
                {"id": sid, "ts": now.isoformat(), "b": "[]", "p": plan, "exp": expires},
            )
            await db.execute(
                text(
                    "INSERT INTO feedback_tokens (token, session_id, created_at, expires_at) "
                    "VALUES (:tok, :sid, :ts, :exp)"
                ),
                {"tok": "auth-share-c", "sid": sid, "ts": now.isoformat(), "exp": expires},
            )
            await db.commit()

        r1 = await client.post(f"/api/plan/{sid}/share?token=auth-share-c")
        share_tok = r1.json()["share_token"]

        r2 = await client.get(f"/api/plan/shared/{share_tok}")
        assert len(r2.json()["next_steps"]) == 10
