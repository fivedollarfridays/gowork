"""S12a end-to-end integration tests — the full worker-companion daily loop (T12.32).

Purpose
-------
Prove the S12a stack composes across module boundaries. Four parametrized
flows run against a fresh sqlite DB (m001 + m002 + m003), both
Montgomery and Fort Worth, and six standalone contract assertions
cover the integration seams unit tests can't observe alone:

  1. Appointment lifecycle: placeholder -> fill -> attended -> outcome.
  2. Stall scenario: 4-day gap -> SOFT -> digest surfaces stall section.
  3. Nightly cycle: retro -> compose -> mock SendGrid -> nightly_run_log.
  4. Both-city parametrization (flows above run once per city).

Contract tests (standalone):
  * Route-collision: /api/job-applications vs /api/jobs/{id}.
  * Two-caller pathway hook: /api/pathway AND /api/plan/{sid}/intelligence.
  * k-anonymity: single-session segment -> {count: null, suppressed: true}.
  * Auto-advance suppression: recent auto_advance outcome ignored.
  * City-scope on orchestrator: seed two cities, run one, other untouched.
  * Event emission: mark_attended -> spy handler receives payload.

Test hygiene
------------
* Each test gets a fresh temp DB via ``tmp_path``.
* Event-bus subscribers are cleared before/after each test.
* SendGrid is replaced with a recording spy — no network IO ever.
* Runtime target: entire file under 60s.

Shared helpers live in :mod:`tests._s12a_e2e_helpers` (not picked up by
pytest collection) to keep this file inside the arch file-size limit.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core import events
from app.core.migrations import runner
from app.modules.appointments import scheduler as appt_scheduler
from app.modules.appointments.outcomes_listener import register_outcomes_listener
from app.modules.appointments.types import Appointment
from app.modules.common.temporal_types import (
    AppointmentStatus,
    AppointmentType,
    StallLevel,
)
from app.modules.engagement.stall_detector import compute_stall_for_session
from app.modules.jobs import applications as job_applications
from app.modules.jobs.funnel_analytics import (
    SuppressedCell,
    compute_community_funnel,
)
from app.modules.outcomes.tracker import OutcomeTracker
from tests._s12a_e2e_helpers import (
    build_appts_client,
    build_multi_router_client,
    insert_outcome,
    install_sendgrid_spy,
    seed_session,
    seed_session_async,
)


# -------------------- Constants --------------------


_SESSION_A = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
_SESSION_B = "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"
_TOKEN_A = "tok-aaaaa"
_TOKEN_B = "tok-bbbbb"

_CITIES = ["montgomery", "fort-worth"]
_CITY_TO_BARRIER = {
    "montgomery": "expunction",
    "fort-worth": "nondisclosure",
}
_CITY_TO_COURT = {
    "montgomery": "Alabama",
    "fort-worth": "Texas",
}


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _isolate_event_bus():
    """Wipe all event subscribers around each test to prevent bleed-over."""
    events.clear_all_subscribers()
    yield
    events.clear_all_subscribers()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    """Fresh sqlite DB with m001 + m002 + m003 applied."""
    path = str(tmp_path / "e2e.db")
    runner.apply_pending(path)
    return path


# -------------------- Per-flow helpers (kept narrow for <50 lines each) --------


def _create_placeholder_via_route(
    client: TestClient, city: str,
) -> dict:
    """Step 1-2 of Flow 1: POST /from-pathway → returns placeholder dict."""
    resp = client.post(
        f"/api/appointments/from-pathway"
        f"?session_id={_SESSION_A}&token={_TOKEN_A}&city={city}",
    )
    assert resp.status_code == 200
    placeholders = resp.json()
    assert len(placeholders) == 1
    placeholder = placeholders[0]
    assert placeholder["source"] == "pathway_auto"
    assert placeholder["starts_at"] is None
    assert placeholder["barrier_link"] == _CITY_TO_BARRIER[city]
    assert _CITY_TO_COURT[city] in placeholder["title"]
    return placeholder


def _fill_placeholder_via_route(
    client: TestClient, appt_id: int, court_label: str,
) -> None:
    """Step 3 of Flow 1: PATCH fills starts_at + ends_at + location_name."""
    starts = datetime.now(timezone.utc) + timedelta(days=2)
    ends = starts + timedelta(hours=1)
    resp = client.patch(
        f"/api/appointments/{appt_id}?token={_TOKEN_A}",
        json={
            "starts_at": starts.isoformat(),
            "ends_at": ends.isoformat(),
            "location_name": f"{court_label} Circuit Court",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["starts_at"] is not None


def _mark_attended_via_route(client: TestClient, appt_id: int) -> None:
    """Step 4 of Flow 1: POST /{id}/attended."""
    resp = client.post(
        f"/api/appointments/{appt_id}/attended?token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "attended"


def _assert_attendance_outcome_recorded(
    db_path: str, barrier: str,
) -> None:
    """Step 5-6 of Flow 1: outcomes_records contains appointment_attended."""
    records = OutcomeTracker(db_path).list_by_session(_SESSION_A)
    signal_types = [r.signal_type for r in records]
    assert "appointment_attended" in signal_types
    rec = next(
        r for r in records if r.signal_type == "appointment_attended"
    )
    assert rec.resource_ratings.get(barrier) is True


def _make_attended_appointment(
    db_path: str, barrier: str,
) -> None:
    """Flow 3 seed helper: a real attended appointment from 6h ago."""
    starts = datetime.now(timezone.utc) - timedelta(hours=6)
    ends = starts + timedelta(hours=1)
    appt = Appointment(
        session_id=_SESSION_A,
        type=AppointmentType.COURT_HEARING,
        title="Court hearing", starts_at=starts, ends_at=ends,
        location_name="Courthouse", barrier_link=barrier,
        status=AppointmentStatus.SCHEDULED, source="user",
    )
    stored = appt_scheduler.create(_SESSION_A, appt, db_path=db_path)
    appt_scheduler.mark_attended(stored.id, db_path=db_path)


def _read_nightly_row(db_path: str) -> tuple[str, int, int]:
    """Read (city, sessions_processed, emails_sent) from nightly_run_log."""
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT city, sessions_processed, emails_sent "
            "FROM nightly_run_log",
        ).fetchone()
    finally:
        conn.close()
    assert row is not None, "no nightly_run_log row written"
    return (row[0], row[1], row[2])


# ====================================================================
# FLOW 1 — Appointment lifecycle (placeholder -> fill -> attended)
# ====================================================================


@pytest.mark.parametrize("city", _CITIES)
def test_flow1_appointment_lifecycle_end_to_end(
    db_path: str, monkeypatch: pytest.MonkeyPatch, city: str,
) -> None:
    """Placeholder -> filled -> attended with outcome record + status."""
    register_outcomes_listener(db_path)
    barrier = _CITY_TO_BARRIER[city]
    seed_session(
        db_path, _SESSION_A, _TOKEN_A,
        barriers=[barrier], city=city,
    )
    client = build_appts_client(db_path, monkeypatch)

    placeholder = _create_placeholder_via_route(client, city)
    _fill_placeholder_via_route(
        client, placeholder["id"], _CITY_TO_COURT[city],
    )
    _mark_attended_via_route(client, placeholder["id"])
    _assert_attendance_outcome_recorded(db_path, barrier)


# ====================================================================
# FLOW 2 — Stall scenario (4-day gap -> SOFT -> digest section)
# ====================================================================


@pytest.mark.parametrize("city", _CITIES)
def test_flow2_stall_soft_surfaces_in_digest(
    db_path: str, monkeypatch: pytest.MonkeyPatch, city: str,
) -> None:
    """4-day-old real signal → SOFT → compose_digest renders stall section."""
    barrier = _CITY_TO_BARRIER[city]
    seed_session(
        db_path, _SESSION_A, _TOKEN_A,
        barriers=[barrier], city=city,
    )
    # Last progress signal 4 days ago → SOFT (>=3 days, <7 days).
    four_days_ago = datetime.now(timezone.utc) - timedelta(days=4)
    insert_outcome(
        db_path, _SESSION_A, "plan_followed",
        created_at=four_days_ago, city=city,
    )

    stall = compute_stall_for_session(_SESSION_A, db_path=db_path)
    assert stall.stall_level == StallLevel.SOFT
    assert stall.days_stalled == 4

    # Compose digest via preview endpoint → stall section included.
    client = build_multi_router_client(db_path, monkeypatch)
    resp = client.get(
        f"/api/engagement/preview-digest"
        f"?session_id={_SESSION_A}&token={_TOKEN_A}",
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["section_counts"]["stall"] >= 1
    html_lower = body["html"].lower()
    assert "check-in" in html_lower
    assert "4 days" in body["html"]


# ====================================================================
# FLOW 3 — Full nightly cycle (retro -> compose -> send -> accounting)
# ====================================================================


@pytest.mark.parametrize("city", _CITIES)
def test_flow3_nightly_cycle_end_to_end(
    db_path: str, monkeypatch: pytest.MonkeyPatch, city: str,
) -> None:
    """Recent attended appt + filed app → nightly run sends digest + logs."""
    register_outcomes_listener(db_path)
    barrier = _CITY_TO_BARRIER[city]
    seed_session(
        db_path, _SESSION_A, _TOKEN_A,
        barriers=[barrier], city=city,
    )
    _make_attended_appointment(db_path, barrier)
    job_applications.create(
        _SESSION_A, match_source="indeed",
        match_url="https://example.com/job/1",
        company="Acme Co", role="Barista", db_path=db_path,
    )

    sent = install_sendgrid_spy(monkeypatch)
    from scripts.nightly_digest import run_nightly_digest
    results = asyncio.run(
        run_nightly_digest(cities=[city], db_path=db_path),
    )

    assert len(results) == 1
    assert results[0].sessions_processed >= 1
    assert results[0].emails_sent >= 1
    assert len(sent) == 1
    assert sent[0]["to"] == "worker@example.com"
    assert sent[0]["session_id"] == _SESSION_A

    logged_city, sessions_processed, emails_sent = _read_nightly_row(db_path)
    assert logged_city == city
    assert sessions_processed >= 1
    assert emails_sent >= 1


# ====================================================================
# CONTRACT 1 — Route collision: /api/job-applications vs /api/jobs/{id}
# ====================================================================


def test_contract_route_collision_distinct_handlers(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Hyphenated /api/job-applications and /api/jobs/{id} hit different handlers."""
    seed_session(
        db_path, _SESSION_A, _TOKEN_A, barriers=[], city="montgomery",
    )
    client = build_multi_router_client(db_path, monkeypatch)

    # POST /api/job-applications (T12.13) creates a job application.
    apps_resp = client.post(
        f"/api/job-applications?token={_TOKEN_A}",
        json={
            "session_id": _SESSION_A, "match_source": "indeed",
            "match_url": "https://example.com/job/1",
            "company": "Acme", "role": "Barista",
        },
    )
    assert apps_resp.status_code == 201
    apps_body = apps_resp.json()
    assert "match_source" in apps_body
    assert "company" in apps_body

    # GET /api/jobs/some_id (listings, different router). Whatever the
    # status, the handler is different: response must NOT have the
    # application-shape fields above.
    jobs_resp = client.get("/api/jobs/nonexistent_job_id")
    assert jobs_resp.status_code != 201
    if jobs_resp.status_code == 200:
        jobs_body = jobs_resp.json()
        assert "match_source" not in jobs_body
        assert "match_url" not in jobs_body


# ====================================================================
# CONTRACT 2 — Two-caller pathway hook (route + plan_intelligence)
# ====================================================================


@pytest.mark.anyio
async def test_contract_pathway_hook_fires_from_both_routes(
    client, test_engine, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """auto_generate_placeholders is invoked by /api/pathway AND /api/plan/.../intelligence."""
    sid = "00000000-0000-4000-8000-ba0e00000001"
    await seed_session_async(
        test_engine, sid, ["dmv_license"], auth_token="tok-both",
    )
    captured: list[dict] = []

    def _fake_linker(session_id, pathway_result, *, city, db_path):
        captured.append({
            "session_id": session_id,
            "barriers": list(pathway_result.barriers_active),
            "city": city,
        })
        return []

    monkeypatch.setattr(
        "app.routes._intelligence_helpers.auto_generate_placeholders",
        _fake_linker,
    )

    r1 = await client.post(
        "/api/pathway?token=tok-both",
        json={"session_id": sid, "current_wage": 10.0},
    )
    assert r1.status_code == 200
    r2 = await client.get(
        f"/api/plan/{sid}/intelligence?token=tok-both&current_wage=10.0",
    )
    assert r2.status_code == 200

    assert len(captured) >= 2
    assert all(c["session_id"] == sid for c in captured)
    assert all("dmv_license" in c["barriers"] for c in captured)


# ====================================================================
# CONTRACT 3 — k-anonymity suppression
# ====================================================================


def test_contract_k_anonymity_single_session_suppressed(
    db_path: str,
) -> None:
    """Single-session segment returns SuppressedCell (count=null, suppressed=true)."""
    seed_session(
        db_path, _SESSION_A, _TOKEN_A,
        barriers=[], city="montgomery",
        cleared_barriers=["dmv_license"],
    )
    job_applications.create(
        _SESSION_A, match_source="indeed",
        match_url="https://example.com/j/1",
        company="Acme", role="Barista", db_path=db_path,
    )

    result = compute_community_funnel(
        "montgomery", segment_by="cleared_barriers", db_path=db_path,
    )
    assert "dmv_license" in result
    cell = result["dmv_license"]
    assert isinstance(cell, SuppressedCell)
    serialized = cell.model_dump()
    assert serialized["count"] is None
    assert serialized["suppressed"] is True
    assert serialized["reason"] == "k_anonymity_min_5"


# ====================================================================
# CONTRACT 4 — Auto-advance suppression on stall
# ====================================================================


def test_contract_auto_advance_filtered_from_stall_signals(
    db_path: str,
) -> None:
    """Recent appointment_auto_advance is ignored; real 10d signal drives MEDIUM."""
    seed_session(
        db_path, _SESSION_A, _TOKEN_A,
        barriers=["dmv_license"], city="montgomery",
    )
    now = datetime.now(timezone.utc)
    insert_outcome(
        db_path, _SESSION_A, "plan_followed",
        created_at=now - timedelta(days=10), city="montgomery",
    )
    insert_outcome(
        db_path, _SESSION_A, "appointment_auto_advance",
        created_at=now - timedelta(hours=12), city="montgomery",
    )

    stall = compute_stall_for_session(_SESSION_A, db_path=db_path, now=now)
    # If auto_advance leaked through, days_stalled would be 0 / NONE.
    assert stall.stall_level == StallLevel.MEDIUM
    assert stall.days_stalled == 10


# ====================================================================
# CONTRACT 5 — City scope on orchestrator
# ====================================================================


def test_contract_orchestrator_respects_city_scope(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Seed two cities; run for montgomery only; fort-worth untouched."""
    seed_session(
        db_path, _SESSION_A, _TOKEN_A,
        barriers=["expunction"], city="montgomery",
        email="mty@example.com",
    )
    seed_session(
        db_path, _SESSION_B, _TOKEN_B,
        barriers=["nondisclosure"], city="fort-worth",
        email="ftw@example.com",
    )
    sent = install_sendgrid_spy(monkeypatch)

    from scripts.nightly_digest import run_nightly_digest
    results = asyncio.run(
        run_nightly_digest(cities=["montgomery"], db_path=db_path),
    )

    assert len(results) == 1
    assert results[0].city == "montgomery"
    assert results[0].sessions_processed == 1
    assert len(sent) == 1
    assert sent[0]["to"] == "mty@example.com"
    assert sent[0]["session_id"] == _SESSION_A

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT city FROM nightly_run_log").fetchall()
    finally:
        conn.close()
    cities_logged = {r[0] for r in rows}
    assert cities_logged == {"montgomery"}


# ====================================================================
# CONTRACT 6 — Event emission on appointment.attended
# ====================================================================


def test_contract_appointment_attended_emits_event(db_path: str) -> None:
    """Spy on appointment.attended; mark_attended triggers it with full payload."""
    seed_session(
        db_path, _SESSION_A, _TOKEN_A,
        barriers=["dmv_license"], city="montgomery",
    )
    starts = datetime.now(timezone.utc) + timedelta(hours=1)
    ends = starts + timedelta(hours=1)
    appt = Appointment(
        session_id=_SESSION_A,
        type=AppointmentType.DMV, title="DMV visit",
        starts_at=starts, ends_at=ends,
        location_name="ALEA office", barrier_link="dmv_license",
        status=AppointmentStatus.SCHEDULED, source="user",
    )
    stored = appt_scheduler.create(_SESSION_A, appt, db_path=db_path)

    captured: list[dict] = []

    def _spy(payload: dict) -> None:
        captured.append(payload)

    events.subscribe("appointment.attended", _spy)
    appt_scheduler.mark_attended(stored.id, db_path=db_path)

    assert len(captured) == 1
    payload = captured[0]
    assert payload["session_id"] == _SESSION_A
    assert payload["id"] == stored.id
    assert payload["status"] == "attended"


# Silence unused-json warning — json module kept for potential future expansion.
_ = json
