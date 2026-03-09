"""Tests for action plan progress tracking — T31.5."""

import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session_factory
from app.core.progress_queries import (
    get_action_checklist,
    store_previous_plan,
    update_action_checklist,
)
from app.core.queries import create_session, get_session_by_id, update_session_plan


@pytest.fixture
async def db_session(test_engine):
    factory = get_async_session_factory()
    async with factory() as session:
        yield session


def _session_data():
    return {
        "barriers": json.dumps(["credit"]),
        "qualifications": "Warehouse experience",
    }


class TestSessionTTL:
    @pytest.mark.anyio
    async def test_session_expires_in_30_days(self, db_session):
        sid = await create_session(db_session, _session_data())
        row = await get_session_by_id(db_session, sid)
        assert row is not None
        expires = datetime.fromisoformat(row["expires_at"])
        created = datetime.fromisoformat(row["created_at"])
        delta = expires - created
        assert delta >= timedelta(days=29)
        assert delta <= timedelta(days=31)


class TestActionChecklist:
    @pytest.mark.anyio
    async def test_checklist_empty_by_default(self, db_session):
        sid = await create_session(db_session, _session_data())
        checklist = await get_action_checklist(db_session, sid)
        assert checklist == {}

    @pytest.mark.anyio
    async def test_update_and_retrieve_checklist(self, db_session):
        sid = await create_session(db_session, _session_data())
        checklist = {"week_1_2:0": True, "month_1:0": False}
        await update_action_checklist(db_session, sid, checklist)
        result = await get_action_checklist(db_session, sid)
        assert result == checklist

    @pytest.mark.anyio
    async def test_update_checklist_overwrites(self, db_session):
        sid = await create_session(db_session, _session_data())
        await update_action_checklist(db_session, sid, {"week_1_2:0": True})
        await update_action_checklist(db_session, sid, {"week_1_2:0": True, "month_1:0": True})
        result = await get_action_checklist(db_session, sid)
        assert result["week_1_2:0"] is True
        assert result["month_1:0"] is True


class TestPreviousPlan:
    @pytest.mark.anyio
    async def test_store_previous_plan(self, db_session):
        sid = await create_session(db_session, _session_data())
        plan = {"action_plan": {"phases": []}}
        await update_session_plan(db_session, sid, json.dumps(plan))
        await store_previous_plan(db_session, sid)
        row = await get_session_by_id(db_session, sid)
        assert row is not None
        prev = json.loads(row["previous_plan"])
        assert prev == plan

    @pytest.mark.anyio
    async def test_store_previous_plan_when_no_plan(self, db_session):
        sid = await create_session(db_session, _session_data())
        await store_previous_plan(db_session, sid)
        row = await get_session_by_id(db_session, sid)
        assert row["previous_plan"] is None


class TestPatchEndpoint:
    @pytest.mark.anyio
    async def test_patch_toggles_action(self, client):
        # Create session via assessment endpoint
        resp = await client.post("/api/assessment/", json={
            "zip_code": "36104",
            "employment_status": "unemployed",
            "barriers": {"credit": True},
            "work_history": "",
            "target_industries": [],
            "has_vehicle": False,
            "schedule_constraints": {"available_days": ["monday"], "available_hours": "daytime"},
        })
        assert resp.status_code == 201
        data = resp.json()
        sid = data["session_id"]
        token = data.get("feedback_token", "")

        # PATCH to toggle an action
        resp = await client.patch(
            f"/api/plan/{sid}/actions?token={token}",
            json={"action_key": "week_1_2:0", "completed": True},
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["checklist"]["week_1_2:0"] is True

    @pytest.mark.anyio
    async def test_patch_requires_token(self, client):
        resp = await client.patch(
            "/api/plan/nonexistent/actions",
            json={"action_key": "week_1_2:0", "completed": True},
        )
        assert resp.status_code == 422 or resp.status_code == 401

    @pytest.mark.anyio
    async def test_get_plan_includes_checklist(self, client):
        resp = await client.post("/api/assessment/", json={
            "zip_code": "36104",
            "employment_status": "unemployed",
            "barriers": {"credit": True},
            "work_history": "",
            "target_industries": [],
            "has_vehicle": False,
            "schedule_constraints": {"available_days": ["monday"], "available_hours": "daytime"},
        })
        assert resp.status_code == 201
        data = resp.json()
        sid = data["session_id"]
        token = data.get("feedback_token", "")

        # Set a checklist item
        await client.patch(
            f"/api/plan/{sid}/actions?token={token}",
            json={"action_key": "week_1_2:0", "completed": True},
        )

        # GET plan should include checklist
        resp = await client.get(f"/api/plan/{sid}?token={token}")
        assert resp.status_code == 200
        plan_data = resp.json()
        assert "action_checklist" in plan_data
        assert plan_data["action_checklist"]["week_1_2:0"] is True
