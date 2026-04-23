"""Tests for the pathway -> appointment auto-linker (T12.9).

Covers placeholder generation, idempotency, reconciliation, and the
route-level hook wiring in both `routes/pathway.py` and
`routes/plan_intelligence.py`.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core import events
from app.core.migrations import runner
from app.modules.appointments import scheduler
from app.modules.appointments.barrier_linker import (
    auto_generate_placeholders,
    find_placeholder_matches,
    validate_patch,
)
from app.modules.appointments.types import Appointment
from app.modules.common.temporal_types import (
    AppointmentStatus,
    AppointmentType,
)
from app.modules.pathway.types import PathwayResult


_SESSION = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _isolate_event_bus() -> None:
    events.clear_all_subscribers()
    yield
    events.clear_all_subscribers()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "linker.db")
    runner.apply_pending(path)
    _seed_session(path, _SESSION)
    return path


def _seed_session(path: str, session_id: str) -> None:
    conn = sqlite3.connect(path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, now, "[]", now),
        )
        conn.commit()
    finally:
        conn.close()


def _pathway_result(barriers: list[str]) -> PathwayResult:
    """Minimal PathwayResult for barrier-based placeholder generation."""
    return PathwayResult(
        pathways=[],
        current_wage=0.0,
        current_net_monthly=0.0,
        barriers_active=list(barriers),
    )


# -------------------- Placeholder generation --------------------


def test_placeholder_for_expunction_AL(db_path: str) -> None:
    """Expunction barrier in Montgomery -> court_hearing placeholder."""
    created = auto_generate_placeholders(
        _SESSION, _pathway_result(["expunction"]),
        city="montgomery", db_path=db_path,
    )
    assert len(created) == 1
    placeholder = created[0]
    assert placeholder.type == AppointmentType.COURT_HEARING
    assert placeholder.source == "pathway_auto"
    assert placeholder.starts_at is None
    assert placeholder.barrier_link == "expunction"
    assert "Alabama circuit court" in placeholder.title or "Alabama" in placeholder.title


def test_placeholder_for_nondisclosure_TX(db_path: str) -> None:
    """Nondisclosure barrier in Fort Worth -> court_hearing placeholder."""
    created = auto_generate_placeholders(
        _SESSION, _pathway_result(["nondisclosure"]),
        city="fort-worth", db_path=db_path,
    )
    assert len(created) == 1
    placeholder = created[0]
    assert placeholder.type == AppointmentType.COURT_HEARING
    assert placeholder.barrier_link == "nondisclosure"
    assert "Texas" in placeholder.title


def test_placeholder_for_benefits_recert_AL(db_path: str) -> None:
    """Benefits recert in Montgomery mentions DHR."""
    created = auto_generate_placeholders(
        _SESSION, _pathway_result(["benefits_recert"]),
        city="montgomery", db_path=db_path,
    )
    assert len(created) == 1
    placeholder = created[0]
    assert placeholder.type == AppointmentType.BENEFITS_RECERT
    assert placeholder.barrier_link == "benefits_recert"
    assert "DHR" in placeholder.title


def test_placeholder_for_benefits_recert_TX(db_path: str) -> None:
    """Benefits recert in Fort Worth mentions HHSC."""
    created = auto_generate_placeholders(
        _SESSION, _pathway_result(["benefits_recert"]),
        city="fort-worth", db_path=db_path,
    )
    assert len(created) == 1
    assert "HHSC" in created[0].title


def test_placeholder_for_dmv(db_path: str) -> None:
    """dmv_license barrier -> dmv-type placeholder."""
    created = auto_generate_placeholders(
        _SESSION, _pathway_result(["dmv_license"]),
        city="montgomery", db_path=db_path,
    )
    assert len(created) == 1
    assert created[0].type == AppointmentType.DMV
    assert created[0].barrier_link == "dmv_license"


def test_placeholder_for_childcare_intake(db_path: str) -> None:
    """childcare_intake barrier -> childcare_intake placeholder."""
    created = auto_generate_placeholders(
        _SESSION, _pathway_result(["childcare_intake"]),
        city="montgomery", db_path=db_path,
    )
    assert len(created) == 1
    assert created[0].type == AppointmentType.CHILDCARE_INTAKE
    assert created[0].barrier_link == "childcare_intake"


def test_credit_dispute_barrier_skipped(db_path: str) -> None:
    """credit_dispute has no scheduled event — no placeholder."""
    created = auto_generate_placeholders(
        _SESSION, _pathway_result(["credit_dispute"]),
        city="montgomery", db_path=db_path,
    )
    assert created == []


def test_unknown_barrier_skipped(db_path: str) -> None:
    """Unknown barriers are ignored, no exception."""
    created = auto_generate_placeholders(
        _SESSION, _pathway_result(["no_such_barrier", "also_unknown"]),
        city="montgomery", db_path=db_path,
    )
    assert created == []


# -------------------- Idempotency --------------------


def test_idempotent_no_duplicates(db_path: str) -> None:
    """Running auto_generate_placeholders twice produces no duplicates."""
    first = auto_generate_placeholders(
        _SESSION, _pathway_result(["expunction", "dmv_license"]),
        city="montgomery", db_path=db_path,
    )
    assert len(first) == 2

    second = auto_generate_placeholders(
        _SESSION, _pathway_result(["expunction", "dmv_license"]),
        city="montgomery", db_path=db_path,
    )
    assert second == []

    all_appts = scheduler.list_by_session(_SESSION, db_path=db_path)
    types_links = {(a.type, a.barrier_link) for a in all_appts}
    assert types_links == {
        (AppointmentType.COURT_HEARING, "expunction"),
        (AppointmentType.DMV, "dmv_license"),
    }


# -------------------- Reconciliation (find_placeholder_matches) --------------------


def test_find_placeholder_matches_same_type_and_barrier(db_path: str) -> None:
    """A real appointment matches an existing placeholder of same (type, barrier)."""
    auto_generate_placeholders(
        _SESSION, _pathway_result(["dmv_license"]),
        city="montgomery", db_path=db_path,
    )
    now = datetime.now(timezone.utc)
    real = Appointment(
        session_id=_SESSION,
        type=AppointmentType.DMV,
        title="DMV visit",
        starts_at=now + timedelta(days=5),
        ends_at=now + timedelta(days=5, hours=1),
        location_name="ALEA office",
        barrier_link="dmv_license",
        status=AppointmentStatus.SCHEDULED,
        source="user",
    )
    matches = find_placeholder_matches(real, db_path=db_path)
    assert len(matches) == 1
    assert matches[0].barrier_link == "dmv_license"
    assert matches[0].source == "pathway_auto"
    assert matches[0].starts_at is None


def test_find_placeholder_matches_ignores_filled(db_path: str) -> None:
    """Placeholder that already has starts_at set is not a match."""
    auto_generate_placeholders(
        _SESSION, _pathway_result(["dmv_license"]),
        city="montgomery", db_path=db_path,
    )
    placeholders = [
        a for a in scheduler.list_by_session(_SESSION, db_path=db_path)
        if a.source == "pathway_auto"
    ]
    assert len(placeholders) == 1
    # Fill the placeholder's starts_at via generic update.
    now = datetime.now(timezone.utc)
    scheduler.update(
        placeholders[0].id, db_path=db_path,
        starts_at=(now + timedelta(days=3)).isoformat(),
        ends_at=(now + timedelta(days=3, hours=1)).isoformat(),
        location_name="ALEA",
    )

    real = Appointment(
        session_id=_SESSION,
        type=AppointmentType.DMV,
        title="DMV visit",
        starts_at=now + timedelta(days=7),
        ends_at=now + timedelta(days=7, hours=1),
        location_name="ALEA",
        barrier_link="dmv_license",
        status=AppointmentStatus.SCHEDULED,
        source="user",
    )
    matches = find_placeholder_matches(real, db_path=db_path)
    assert matches == []


def test_find_placeholder_matches_ignores_different_type(db_path: str) -> None:
    """Placeholder with different type is not a match."""
    auto_generate_placeholders(
        _SESSION, _pathway_result(["dmv_license"]),
        city="montgomery", db_path=db_path,
    )
    now = datetime.now(timezone.utc)
    real = Appointment(
        session_id=_SESSION,
        type=AppointmentType.COURT_HEARING,  # different
        title="Court",
        starts_at=now + timedelta(days=2),
        ends_at=now + timedelta(days=2, hours=1),
        location_name="Court",
        barrier_link="dmv_license",
        status=AppointmentStatus.SCHEDULED,
        source="user",
    )
    assert find_placeholder_matches(real, db_path=db_path) == []


# -------------------- validate_patch --------------------


def _placeholder(session_id: str = _SESSION) -> Appointment:
    return Appointment(
        session_id=session_id,
        type=AppointmentType.DMV,
        title="DMV placeholder",
        starts_at=None,
        source="pathway_auto",
        barrier_link="dmv_license",
        status=AppointmentStatus.SCHEDULED,
    )


def test_validate_patch_rejects_session_change() -> None:
    existing = _placeholder()
    with pytest.raises(ValueError, match="session_id"):
        validate_patch(existing, {"session_id": "other-session"})


def test_validate_patch_rejects_type_change() -> None:
    existing = _placeholder()
    with pytest.raises(ValueError, match="type"):
        validate_patch(existing, {"type": AppointmentType.COURT_HEARING})


def test_validate_patch_rejects_barrier_link_change() -> None:
    existing = _placeholder()
    with pytest.raises(ValueError, match="barrier_link"):
        validate_patch(existing, {"barrier_link": "expunction"})


def test_validate_patch_accepts_starts_at_fill() -> None:
    existing = _placeholder()
    now = datetime.now(timezone.utc)
    # Should not raise.
    validate_patch(existing, {
        "starts_at": now + timedelta(days=2),
        "ends_at": now + timedelta(days=2, hours=1),
        "location_name": "ALEA office",
    })


# -------------------- Hook integration (routes) --------------------


async def _seed_session_via_engine(
    test_engine,
    session_id: str,
    barriers: list[str],
    auth_token: str,
) -> None:
    """Seed a session + feedback token via the async engine (for route tests)."""
    from sqlalchemy import text

    from app.core.database import get_async_session_factory

    factory = get_async_session_factory()
    async with factory() as db:
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(days=30)).isoformat()
        plan = json.dumps({
            "plan_id": "test", "session_id": session_id,
            "barriers": [], "immediate_next_steps": ["Go"],
        })
        await db.execute(
            text(
                "INSERT INTO sessions (id, created_at, barriers, plan, expires_at) "
                "VALUES (:id, :ts, :b, :p, :exp)"
            ),
            {
                "id": session_id, "ts": now.isoformat(),
                "b": json.dumps(barriers), "p": plan, "exp": expires,
            },
        )
        await db.execute(
            text(
                "INSERT INTO feedback_tokens (token, session_id, created_at, expires_at) "
                "VALUES (:tok, :sid, :ts, :exp)"
            ),
            {
                "tok": auth_token, "sid": session_id,
                "ts": now.isoformat(), "exp": expires,
            },
        )
        await db.commit()


@pytest.mark.anyio
async def test_hook_in_pathway_route(client, test_engine, monkeypatch) -> None:
    """Pathway route triggers auto_generate_placeholders with session + pathway."""
    sid = "00000000-0000-4000-8000-ba0e00000001"
    await _seed_session_via_engine(
        test_engine, sid, ["dmv_license"], auth_token="tok-hook-1",
    )

    captured: dict = {}

    def _fake_linker(session_id, pathway_result, *, city, db_path):
        captured["session_id"] = session_id
        captured["city"] = city
        captured["barriers"] = list(pathway_result.barriers_active)
        return []

    monkeypatch.setattr(
        "app.routes._intelligence_helpers.auto_generate_placeholders", _fake_linker,
    )
    resp = await client.post(
        "/api/pathway?token=tok-hook-1",
        json={"session_id": sid, "current_wage": 10.0},
    )
    assert resp.status_code == 200
    assert captured["session_id"] == sid
    assert "dmv_license" in captured["barriers"]


@pytest.mark.anyio
async def test_hook_in_plan_intelligence_route(client, test_engine, monkeypatch) -> None:
    """Plan intelligence route also triggers auto_generate_placeholders."""
    sid = "00000000-0000-4000-8000-ba0e00000002"
    await _seed_session_via_engine(
        test_engine, sid, ["dmv_license"], auth_token="tok-hook-2",
    )

    captured: dict = {}

    def _fake_linker(session_id, pathway_result, *, city, db_path):
        captured["session_id"] = session_id
        return []

    monkeypatch.setattr(
        "app.routes._intelligence_helpers.auto_generate_placeholders", _fake_linker,
    )
    resp = await client.get(
        f"/api/plan/{sid}/intelligence?token=tok-hook-2&current_wage=10.0",
    )
    assert resp.status_code == 200
    assert captured["session_id"] == sid


@pytest.mark.anyio
async def test_hook_failure_does_not_break_pathway_response(
    client, test_engine, monkeypatch,
) -> None:
    """Linker exception is swallowed; pathway response still returns 200."""
    sid = "00000000-0000-4000-8000-ba0e00000003"
    await _seed_session_via_engine(
        test_engine, sid, ["dmv_license"], auth_token="tok-hook-3",
    )

    def _boom(*args, **kwargs):
        raise RuntimeError("deliberate linker failure")

    monkeypatch.setattr(
        "app.routes._intelligence_helpers.auto_generate_placeholders", _boom,
    )
    resp = await client.post(
        "/api/pathway?token=tok-hook-3",
        json={"session_id": sid, "current_wage": 10.0},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "pathways" in body


@pytest.mark.anyio
async def test_hook_failure_does_not_break_intelligence_response(
    client, test_engine, monkeypatch,
) -> None:
    """Linker exception in plan_intelligence is swallowed; 200 returned."""
    sid = "00000000-0000-4000-8000-ba0e00000004"
    await _seed_session_via_engine(
        test_engine, sid, ["dmv_license"], auth_token="tok-hook-4",
    )

    def _boom(*args, **kwargs):
        raise RuntimeError("deliberate linker failure")

    monkeypatch.setattr(
        "app.routes._intelligence_helpers.auto_generate_placeholders", _boom,
    )
    resp = await client.get(
        f"/api/plan/{sid}/intelligence?token=tok-hook-4&current_wage=10.0",
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "pathway" in body
