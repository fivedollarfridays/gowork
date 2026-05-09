"""Tests for the admin feedback inbox + flagged-queue endpoints (T26.3).

Covers the five routes mounted under ``/api/admin/feedback/...``, all
gated by :func:`require_role("admin")`:

* ``GET    /api/admin/feedback/flagged?city=<slug>``
* ``POST   /api/admin/feedback/flagged/{resource_id}/approve``
* ``POST   /api/admin/feedback/flagged/{resource_id}/confirm-hide``
* ``GET    /api/admin/feedback/visits?reviewed=<bool>&limit=<n>&offset=<n>``
* ``POST   /api/admin/feedback/visits/{id}/mark-reviewed``

T26.2 owns the ``routes/__init__.py`` edit that registers
``admin_feedback_router`` on the production app, so these tests mount
the router on a fresh FastAPI app to stay independent of T26.2's
landing order. The DB layer is the real one — the test_engine fixture
swaps the global engine to a fresh sqlite file, so query helpers run
end-to-end against the schema.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import queries_accounts, queries_roles
from app.core.accounts_schema import apply_ddl as apply_accounts_ddl
from app.core.roles_schema import apply_ddl as apply_roles_ddl
from app.routes._auth_claim_helpers import (
    SESSION_COOKIE_NAME,
    build_account_cookie_value,
)


# -------------------- Fixtures --------------------


@pytest.fixture
async def feedback_engine(test_engine):
    """test_engine + accounts + roles DDL applied on top."""
    async with test_engine.begin() as conn:
        await conn.run_sync(apply_accounts_ddl)
        await conn.run_sync(apply_roles_ddl)
    return test_engine


@pytest.fixture
def session_factory(feedback_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        feedback_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.fixture
async def admin_feedback_client(feedback_engine):
    """Fresh FastAPI app mounting only the T26.3 router.

    Decoupled from ``app.main.app`` because T26.2 owns the
    ``routes/__init__.py`` registration this wave; mounting locally
    means these tests don't depend on T26.2 landing first.
    """
    from app.routes.admin_feedback import router

    app = FastAPI()
    app.include_router(router)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# -------------------- Helpers --------------------


async def _seed_admin(
    session: AsyncSession, email: str
) -> tuple[int, str]:
    account_id = await queries_accounts.create_account(session, email=email)
    await queries_roles.grant_role(session, account_id, "admin")
    return account_id, build_account_cookie_value(account_id)


async def _seed_non_admin(
    session: AsyncSession, email: str
) -> tuple[int, str]:
    account_id = await queries_accounts.create_account(session, email=email)
    return account_id, build_account_cookie_value(account_id)


async def _seed_resource(
    session: AsyncSession,
    *,
    name: str,
    city: str = "fort-worth",
    health_status: str = "healthy",
    category: str = "social_service",
) -> int:
    result = await session.execute(
        text(
            "INSERT INTO resources (name, category, city, health_status) "
            "VALUES (:n, :c, :city, :hs) RETURNING id"
        ),
        {"n": name, "c": category, "city": city, "hs": health_status},
    )
    rid = int(result.scalar_one())
    await session.commit()
    return rid


async def _seed_resource_feedback(
    session: AsyncSession,
    *,
    resource_id: int,
    session_id: str,
    helpful: int,
    submitted_at: str | None = None,
    barrier_type: str | None = None,
) -> None:
    ts = submitted_at or datetime.now(timezone.utc).isoformat()
    await session.execute(
        text(
            "INSERT INTO resource_feedback "
            "(resource_id, session_id, helpful, barrier_type, submitted_at) "
            "VALUES (:rid, :sid, :h, :bt, :ts)"
        ),
        {"rid": resource_id, "sid": session_id, "h": helpful,
         "bt": barrier_type, "ts": ts},
    )
    await session.commit()


async def _seed_visit_feedback(
    session: AsyncSession,
    *,
    session_id: str,
    made_it: int = 1,
    plan_accuracy: int = 4,
    reviewed: int = 0,
    action_taken: str | None = None,
    submitted_at: str | None = None,
    free_text: str | None = "ok",
) -> int:
    ts = submitted_at or datetime.now(timezone.utc).isoformat()
    result = await session.execute(
        text(
            "INSERT INTO visit_feedback "
            "(session_id, submitted_at, made_it_to_center, outcomes, "
            "plan_accuracy, free_text, reviewed, action_taken) "
            "VALUES (:sid, :ts, :mit, :out, :acc, :ft, :rev, :act) "
            "RETURNING id"
        ),
        {
            "sid": session_id, "ts": ts, "mit": made_it,
            "out": "[]", "acc": plan_accuracy, "ft": free_text,
            "rev": reviewed, "act": action_taken,
        },
    )
    vid = int(result.scalar_one())
    await session.commit()
    return vid


# -------------------- Auth gating: anonymous / non-admin --------------------


@pytest.mark.anyio
async def test_flagged_anonymous_returns_403(admin_feedback_client):
    resp = await admin_feedback_client.get("/api/admin/feedback/flagged")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_flagged_non_admin_returns_403(
    admin_feedback_client, session_factory
):
    async with session_factory() as session:
        _id, cookie = await _seed_non_admin(session, "u1@example.com")
    resp = await admin_feedback_client.get(
        "/api/admin/feedback/flagged",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_approve_anonymous_returns_403(admin_feedback_client):
    resp = await admin_feedback_client.post(
        "/api/admin/feedback/flagged/1/approve"
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_confirm_hide_anonymous_returns_403(admin_feedback_client):
    resp = await admin_feedback_client.post(
        "/api/admin/feedback/flagged/1/confirm-hide"
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_visits_anonymous_returns_403(admin_feedback_client):
    resp = await admin_feedback_client.get("/api/admin/feedback/visits")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_visits_non_admin_returns_403(
    admin_feedback_client, session_factory
):
    async with session_factory() as session:
        _id, cookie = await _seed_non_admin(session, "u2@example.com")
    resp = await admin_feedback_client.get(
        "/api/admin/feedback/visits",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_mark_reviewed_anonymous_returns_403(admin_feedback_client):
    resp = await admin_feedback_client.post(
        "/api/admin/feedback/visits/1/mark-reviewed"
    )
    assert resp.status_code == 403


# -------------------- Flagged queue happy paths --------------------


@pytest.mark.anyio
async def test_flagged_admin_returns_only_flagged_rows(
    admin_feedback_client, session_factory
):
    """Healthy + watch + hidden rows MUST NOT appear in the queue."""
    async with session_factory() as session:
        flagged_id = await _seed_resource(
            session, name="Flagged FW", city="fort-worth",
            health_status="flagged",
        )
        await _seed_resource(
            session, name="Healthy FW", city="fort-worth",
            health_status="healthy",
        )
        await _seed_resource(
            session, name="Hidden FW", city="fort-worth",
            health_status="hidden",
        )
        await _seed_resource(
            session, name="Watching", city="fort-worth",
            health_status="watch",
        )
        _aid, cookie = await _seed_admin(session, "admin1@example.com")

    resp = await admin_feedback_client.get(
        "/api/admin/feedback/flagged",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "items" in body
    items = body["items"]
    assert len(items) == 1
    assert items[0]["id"] == flagged_id
    assert items[0]["health_status"] == "flagged"
    assert items[0]["name"] == "Flagged FW"


@pytest.mark.anyio
async def test_flagged_filters_by_city(
    admin_feedback_client, session_factory
):
    """`?city=` filter scopes the query."""
    async with session_factory() as session:
        fw_id = await _seed_resource(
            session, name="FW Flag", city="fort-worth",
            health_status="flagged",
        )
        await _seed_resource(
            session, name="Dallas Flag", city="dallas",
            health_status="flagged",
        )
        _aid, cookie = await _seed_admin(session, "admin2@example.com")

    resp = await admin_feedback_client.get(
        "/api/admin/feedback/flagged?city=fort-worth",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == fw_id


@pytest.mark.anyio
async def test_flagged_includes_recent_negative_feedback(
    admin_feedback_client, session_factory
):
    """Recent (≤30d) negative feedback rows MUST surface as context.

    Helpful=1 rows and >30d-old rows MUST NOT appear in the context list.
    """
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(days=2)).isoformat()
    old = (now - timedelta(days=45)).isoformat()

    async with session_factory() as session:
        rid = await _seed_resource(
            session, name="Has Feedback", city="fort-worth",
            health_status="flagged",
        )
        # In-window negative — should appear.
        await _seed_resource_feedback(
            session, resource_id=rid, session_id="s-recent-neg",
            helpful=0, submitted_at=recent, barrier_type="hours",
        )
        # In-window positive — should NOT appear.
        await _seed_resource_feedback(
            session, resource_id=rid, session_id="s-recent-pos",
            helpful=1, submitted_at=recent,
        )
        # Out-of-window negative — should NOT appear.
        await _seed_resource_feedback(
            session, resource_id=rid, session_id="s-old-neg",
            helpful=0, submitted_at=old,
        )
        _aid, cookie = await _seed_admin(session, "admin3@example.com")

    resp = await admin_feedback_client.get(
        "/api/admin/feedback/flagged",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    fb = items[0]["recent_negative_feedback"]
    assert isinstance(fb, list)
    assert len(fb) == 1
    assert fb[0]["session_id"] == "s-recent-neg"
    assert fb[0]["barrier_type"] == "hours"


# -------------------- Flagged mutations --------------------


@pytest.mark.anyio
async def test_approve_clears_flag_to_healthy(
    admin_feedback_client, session_factory
):
    async with session_factory() as session:
        rid = await _seed_resource(
            session, name="To Approve", city="fort-worth",
            health_status="flagged",
        )
        _aid, cookie = await _seed_admin(session, "admin4@example.com")

    resp = await admin_feedback_client.post(
        f"/api/admin/feedback/flagged/{rid}/approve",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["health_status"] == "healthy"

    async with session_factory() as session:
        row = await session.execute(
            text("SELECT health_status FROM resources WHERE id = :id"),
            {"id": rid},
        )
        assert row.scalar_one() == "healthy"


@pytest.mark.anyio
async def test_confirm_hide_sets_hidden(
    admin_feedback_client, session_factory
):
    async with session_factory() as session:
        rid = await _seed_resource(
            session, name="To Hide", city="fort-worth",
            health_status="flagged",
        )
        _aid, cookie = await _seed_admin(session, "admin5@example.com")

    resp = await admin_feedback_client.post(
        f"/api/admin/feedback/flagged/{rid}/confirm-hide",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["health_status"] == "hidden"

    async with session_factory() as session:
        row = await session.execute(
            text("SELECT health_status FROM resources WHERE id = :id"),
            {"id": rid},
        )
        assert row.scalar_one() == "hidden"


@pytest.mark.anyio
async def test_approve_unknown_resource_returns_404(
    admin_feedback_client, session_factory
):
    async with session_factory() as session:
        _aid, cookie = await _seed_admin(session, "admin6@example.com")
    resp = await admin_feedback_client.post(
        "/api/admin/feedback/flagged/99999/approve",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_confirm_hide_unknown_resource_returns_404(
    admin_feedback_client, session_factory
):
    async with session_factory() as session:
        _aid, cookie = await _seed_admin(session, "admin7@example.com")
    resp = await admin_feedback_client.post(
        "/api/admin/feedback/flagged/99999/confirm-hide",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_approve_non_admin_returns_403(
    admin_feedback_client, session_factory
):
    async with session_factory() as session:
        rid = await _seed_resource(
            session, name="Locked", city="fort-worth",
            health_status="flagged",
        )
        _id, cookie = await _seed_non_admin(session, "non1@example.com")
    resp = await admin_feedback_client.post(
        f"/api/admin/feedback/flagged/{rid}/approve",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 403


# -------------------- Visit feedback inbox --------------------


@pytest.mark.anyio
async def test_visits_admin_returns_paginated_list(
    admin_feedback_client, session_factory
):
    async with session_factory() as session:
        for i in range(3):
            await _seed_visit_feedback(session, session_id=f"v{i}")
        _aid, cookie = await _seed_admin(session, "admin8@example.com")

    resp = await admin_feedback_client.get(
        "/api/admin/feedback/visits",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert body["total"] == 3
    assert len(body["items"]) == 3


@pytest.mark.anyio
async def test_visits_filters_by_reviewed_state(
    admin_feedback_client, session_factory
):
    async with session_factory() as session:
        await _seed_visit_feedback(
            session, session_id="reviewed-1", reviewed=1,
            action_taken="contacted candidate",
        )
        await _seed_visit_feedback(
            session, session_id="open-1", reviewed=0,
        )
        await _seed_visit_feedback(
            session, session_id="open-2", reviewed=0,
        )
        _aid, cookie = await _seed_admin(session, "admin9@example.com")

    # reviewed=false
    resp = await admin_feedback_client.get(
        "/api/admin/feedback/visits?reviewed=false",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert {item["session_id"] for item in body["items"]} == {
        "open-1", "open-2",
    }

    # reviewed=true
    resp2 = await admin_feedback_client.get(
        "/api/admin/feedback/visits?reviewed=true",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert body2["total"] == 1
    assert body2["items"][0]["session_id"] == "reviewed-1"
    assert body2["items"][0]["action_taken"] == "contacted candidate"


@pytest.mark.anyio
async def test_visits_pagination_offset_and_limit(
    admin_feedback_client, session_factory
):
    async with session_factory() as session:
        # Submitted_at controls ordering — newest first. Use distinct
        # timestamps so the order is deterministic.
        base = datetime(2026, 5, 1, tzinfo=timezone.utc)
        for i in range(5):
            ts = (base + timedelta(hours=i)).isoformat()
            await _seed_visit_feedback(
                session, session_id=f"p{i}", submitted_at=ts,
            )
        _aid, cookie = await _seed_admin(session, "admin10@example.com")

    resp = await admin_feedback_client.get(
        "/api/admin/feedback/visits?limit=2&offset=1",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["limit"] == 2
    assert body["offset"] == 1
    assert body["total"] == 5
    assert len(body["items"]) == 2
    # Newest-first DESC: index 0 is p4, so offset=1 starts at p3.
    assert body["items"][0]["session_id"] == "p3"
    assert body["items"][1]["session_id"] == "p2"


@pytest.mark.anyio
async def test_visits_limit_capped_at_100(
    admin_feedback_client, session_factory
):
    """Caller-supplied limit > 100 must be clamped (no 422)."""
    async with session_factory() as session:
        await _seed_visit_feedback(session, session_id="any")
        _aid, cookie = await _seed_admin(session, "admin11@example.com")

    resp = await admin_feedback_client.get(
        "/api/admin/feedback/visits?limit=500",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_mark_visit_reviewed_sets_columns(
    admin_feedback_client, session_factory
):
    async with session_factory() as session:
        vid = await _seed_visit_feedback(session, session_id="to-review")
        _aid, cookie = await _seed_admin(session, "admin12@example.com")

    resp = await admin_feedback_client.post(
        f"/api/admin/feedback/visits/{vid}/mark-reviewed",
        json={"action_taken": "called the case manager"},
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["reviewed"] is True
    assert body["action_taken"] == "called the case manager"

    async with session_factory() as session:
        row = await session.execute(
            text(
                "SELECT reviewed, action_taken FROM visit_feedback "
                "WHERE id = :id"
            ),
            {"id": vid},
        )
        r = row.first()
        assert r is not None
        assert r._mapping["reviewed"] == 1
        assert r._mapping["action_taken"] == "called the case manager"


@pytest.mark.anyio
async def test_mark_visit_reviewed_without_action_taken(
    admin_feedback_client, session_factory
):
    """Empty body: reviewed flips to 1; action_taken stays NULL."""
    async with session_factory() as session:
        vid = await _seed_visit_feedback(session, session_id="bare")
        _aid, cookie = await _seed_admin(session, "admin13@example.com")

    resp = await admin_feedback_client.post(
        f"/api/admin/feedback/visits/{vid}/mark-reviewed",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["reviewed"] is True
    assert body["action_taken"] is None


@pytest.mark.anyio
async def test_mark_visit_reviewed_unknown_returns_404(
    admin_feedback_client, session_factory
):
    async with session_factory() as session:
        _aid, cookie = await _seed_admin(session, "admin14@example.com")
    resp = await admin_feedback_client.post(
        "/api/admin/feedback/visits/99999/mark-reviewed",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_mark_visit_reviewed_non_admin_returns_403(
    admin_feedback_client, session_factory
):
    async with session_factory() as session:
        vid = await _seed_visit_feedback(session, session_id="locked")
        _id, cookie = await _seed_non_admin(session, "non2@example.com")
    resp = await admin_feedback_client.post(
        f"/api/admin/feedback/visits/{vid}/mark-reviewed",
        cookies={SESSION_COOKIE_NAME: cookie},
    )
    assert resp.status_code == 403
