"""Tests for POST /api/pathway — career pathway generation endpoint."""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.database import get_async_session_factory


async def _seed_session_with_profile(
    test_engine,
    session_id: str,
    barriers: list[str],
    *,
    auth_token: str,
    benefits_profile: dict | None = None,
) -> str:
    """Insert a session with barriers, plan, and optional benefits profile."""
    factory = get_async_session_factory()
    async with factory() as db:
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(days=30)).isoformat()
        plan = json.dumps({
            "plan_id": "test", "session_id": session_id,
            "barriers": [], "immediate_next_steps": ["Go"],
        })
        bp_json = json.dumps(benefits_profile) if benefits_profile else None
        await db.execute(
            text(
                "INSERT INTO sessions (id, created_at, barriers, plan, expires_at, benefits_profile) "
                "VALUES (:id, :ts, :b, :p, :exp, :bp)"
            ),
            {
                "id": session_id,
                "ts": now.isoformat(),
                "b": json.dumps(barriers),
                "p": plan,
                "exp": expires,
                "bp": bp_json,
            },
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


class TestPathwayEndpoint:
    """POST /api/pathway — career pathway generation."""

    @pytest.mark.anyio
    async def test_generates_pathways(self, client, test_engine):
        """Happy path: returns pathways for valid session with barriers."""
        sid = "00000000-0000-4000-8000-aa0e00000001"
        tok = await _seed_session_with_profile(
            test_engine, sid,
            ["criminal_record", "credit", "transportation"],
            auth_token="path-tok-1",
        )
        resp = await client.post(
            f"/api/pathway?token={tok}",
            json={"session_id": sid, "current_wage": 10.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pathways" in data
        assert isinstance(data["pathways"], list)
        assert len(data["pathways"]) > 0

    @pytest.mark.anyio
    async def test_invalid_token_returns_401(self, client, test_engine):
        """Invalid auth token returns 401."""
        resp = await client.post(
            "/api/pathway?token=bad-token",
            json={
                "session_id": "00000000-0000-4000-8000-aa0e00000002",
                "current_wage": 10.0,
            },
        )
        assert resp.status_code == 401

    @pytest.mark.anyio
    async def test_session_not_found_returns_404(self, client, test_engine):
        """Non-existent session returns 404 (after auth check)."""
        resp = await client.post(
            "/api/pathway?token=any",
            json={
                "session_id": "00000000-0000-4000-8000-aa0e00000003",
                "current_wage": 10.0,
            },
        )
        assert resp.status_code in (401, 404)

    @pytest.mark.anyio
    async def test_zero_wage_accepted(self, client, test_engine):
        """current_wage=0 is valid (unemployed)."""
        sid = "00000000-0000-4000-8000-aa0e00000004"
        tok = await _seed_session_with_profile(
            test_engine, sid,
            ["credit"],
            auth_token="path-tok-4",
        )
        resp = await client.post(
            f"/api/pathway?token={tok}",
            json={"session_id": sid, "current_wage": 0.0},
        )
        assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_negative_wage_rejected(self, client, test_engine):
        """Negative wage should be rejected by validation."""
        sid = "00000000-0000-4000-8000-aa0e00000005"
        tok = await _seed_session_with_profile(
            test_engine, sid,
            ["credit"],
            auth_token="path-tok-5",
        )
        resp = await client.post(
            f"/api/pathway?token={tok}",
            json={"session_id": sid, "current_wage": -5.0},
        )
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_wage_above_max_rejected(self, client, test_engine):
        """Wage above 100.0 should be rejected by validation."""
        sid = "00000000-0000-4000-8000-aa0e00000006"
        tok = await _seed_session_with_profile(
            test_engine, sid,
            ["credit"],
            auth_token="path-tok-6",
        )
        resp = await client.post(
            f"/api/pathway?token={tok}",
            json={"session_id": sid, "current_wage": 150.0},
        )
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_invalid_session_id_format_rejected(self, client, test_engine):
        """Non-UUID session_id should be rejected by validation."""
        resp = await client.post(
            "/api/pathway?token=any",
            json={"session_id": "not-a-uuid", "current_wage": 10.0},
        )
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_missing_token_query_param(self, client, test_engine):
        """Missing token query parameter returns 422."""
        resp = await client.post(
            "/api/pathway",
            json={
                "session_id": "00000000-0000-4000-8000-aa0e00000007",
                "current_wage": 10.0,
            },
        )
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_with_benefits_profile(self, client, test_engine):
        """Session with benefits profile produces pathways with cliff data."""
        sid = "00000000-0000-4000-8000-aa0e00000008"
        bp = {
            "household_size": 3,
            "annual_income": 25000,
            "enrolled_programs": ["snap", "medicaid"],
        }
        tok = await _seed_session_with_profile(
            test_engine, sid,
            ["credit", "childcare"],
            auth_token="path-tok-8",
            benefits_profile=bp,
        )
        resp = await client.post(
            f"/api/pathway?token={tok}",
            json={"session_id": sid, "current_wage": 12.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pathways" in data

    @pytest.mark.anyio
    async def test_empty_barriers_produces_pathways(self, client, test_engine):
        """Session with no barriers still returns pathways (empty steps)."""
        sid = "00000000-0000-4000-8000-aa0e00000009"
        tok = await _seed_session_with_profile(
            test_engine, sid,
            [],
            auth_token="path-tok-9",
        )
        resp = await client.post(
            f"/api/pathway?token={tok}",
            json={"session_id": sid, "current_wage": 15.0},
        )
        assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_malformed_benefits_profile_uses_default(self, client, test_engine):
        """Corrupt benefits_profile falls back to default BenefitsProfile."""
        sid = "00000000-0000-4000-8000-aa0e0000000a"
        factory = get_async_session_factory()
        async with factory() as db:
            now = datetime.now(timezone.utc)
            expires = (now + timedelta(days=30)).isoformat()
            plan = json.dumps({
                "plan_id": "test", "session_id": sid,
                "barriers": [], "immediate_next_steps": [],
            })
            await db.execute(
                text(
                    "INSERT INTO sessions (id, created_at, barriers, plan, expires_at, benefits_profile) "
                    "VALUES (:id, :ts, :b, :p, :exp, :bp)"
                ),
                {
                    "id": sid,
                    "ts": now.isoformat(),
                    "b": json.dumps(["credit"]),
                    "p": plan,
                    "exp": expires,
                    "bp": "not-valid-json",
                },
            )
            await db.execute(
                text(
                    "INSERT INTO feedback_tokens (token, session_id, created_at, expires_at) "
                    "VALUES (:tok, :sid, :ts, :exp)"
                ),
                {"tok": "path-tok-a", "sid": sid, "ts": now.isoformat(), "exp": expires},
            )
            await db.commit()

        resp = await client.post(
            "/api/pathway?token=path-tok-a",
            json={"session_id": sid, "current_wage": 10.0},
        )
        assert resp.status_code == 200
