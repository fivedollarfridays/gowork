"""Tests for appointments.reconcile (T12.25a — past-appointment auto-advance).

Covers the AC items:
- within-grace (no advance)
- beyond-grace (advance + audit row + worker notice + outcome record)
- manual-attended already (no action)
- idempotent (running twice doesn't double-notice)
- stall-suppression: after auto_advance outcome is appended, the existing
  T12.18 stall detector keeps the worker's stall clock pinned to their
  REAL last activity (does not reset to "now" off the auto-advance row)
- orchestrator wiring: step 2.5 calls advance_past_bookings before
  the digest composer runs

Sweep semantics: ``reconcile_session_appointments`` operates per-session
so it composes cleanly into the existing per-session orchestrator loop.
``advance_past_bookings`` is the multi-session sweep entry point.
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
from app.modules.appointments.types import Appointment
from app.modules.common.temporal_types import (
    AppointmentStatus,
    AppointmentType,
    StallLevel,
)
from app.modules.engagement.stall_detector import compute_stall_for_session

_SESSION_A = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
_SESSION_B = "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"
_NOW = datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc)


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _isolate_event_bus():
    events.clear_all_subscribers()
    yield
    events.clear_all_subscribers()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "reconcile.db")
    runner.apply_pending(path)
    _seed_session(path, _SESSION_A, barriers=["dmv"])
    _seed_session(path, _SESSION_B, barriers=["childcare"])
    return path


def _seed_session(path: str, sid: str, *, barriers: list[str]) -> None:
    conn = sqlite3.connect(path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO sessions "
            "(id, created_at, barriers, profile, expires_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (sid, now, json.dumps(barriers), "{}", now),
        )
        conn.commit()
    finally:
        conn.close()


# -------------------- Helpers --------------------


def _create_appt(
    *,
    session_id: str,
    starts_at: datetime,
    db_path: str,
    barrier_link: str | None = "dmv",
    status: AppointmentStatus = AppointmentStatus.SCHEDULED,
) -> Appointment:
    """Insert an appointment with the chosen starts_at and status."""
    appt = Appointment(
        session_id=session_id,
        type=AppointmentType.DMV,
        title="DMV visit",
        starts_at=starts_at,
        ends_at=starts_at + timedelta(hours=1),
        location_name="DMV Office",
        barrier_link=barrier_link,
        status=AppointmentStatus.SCHEDULED,
    )
    stored = scheduler.create(session_id, appt, db_path=db_path)
    if status is AppointmentStatus.ATTENDED:
        return scheduler.mark_attended(stored.id, db_path=db_path)
    return stored


def _engagement_rows(
    db_path: str, *, session_id: str, category: str,
) -> list[dict]:
    """Return engagement_events rows for (session_id, category)."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT session_id, category, payload_json, created_at "
            "FROM engagement_events "
            "WHERE session_id = ? AND category = ? "
            "ORDER BY id ASC",
            (session_id, category),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def _outcome_rows(db_path: str, *, session_id: str) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT session_id, event_type, payload_json, created_at "
            "FROM outcomes_records "
            "WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


# -------------------- Cycle 1: within-grace, no advance --------------------


def test_within_grace_does_not_advance(db_path: str) -> None:
    """starts_at < now but inside the 6h grace → status untouched, no events."""
    from app.modules.appointments.reconcile import (
        reconcile_session_appointments,
    )

    starts = _NOW - timedelta(hours=2)  # 2h ago, well inside 6h grace
    appt = _create_appt(
        session_id=_SESSION_A, starts_at=starts, db_path=db_path,
    )
    result = reconcile_session_appointments(
        _SESSION_A, db_path=db_path, now=_NOW,
    )

    assert result.advanced == 0
    refreshed = scheduler.get(appt.id, db_path=db_path)
    assert refreshed is not None
    assert refreshed.status is AppointmentStatus.SCHEDULED
    assert _engagement_rows(
        db_path, session_id=_SESSION_A, category="appointment_auto_advance",
    ) == []
    assert _engagement_rows(
        db_path, session_id=_SESSION_A,
        category="appointment_auto_missed_notice",
    ) == []


# -------------------- Cycle 2: beyond grace → advance + audit + notice -----


def test_beyond_grace_advances_and_notifies(db_path: str) -> None:
    """starts_at > 6h ago + still scheduled → marked missed, all 3 records."""
    from app.modules.appointments.reconcile import (
        reconcile_session_appointments,
    )

    starts = _NOW - timedelta(hours=8)  # past the 6h grace
    appt = _create_appt(
        session_id=_SESSION_A, starts_at=starts, db_path=db_path,
    )
    result = reconcile_session_appointments(
        _SESSION_A, db_path=db_path, now=_NOW,
    )

    assert result.advanced == 1
    refreshed = scheduler.get(appt.id, db_path=db_path)
    assert refreshed.status is AppointmentStatus.MISSED

    # Audit engagement_event row.
    audits = _engagement_rows(
        db_path, session_id=_SESSION_A, category="appointment_auto_advance",
    )
    assert len(audits) == 1
    payload = json.loads(audits[0]["payload_json"])
    assert payload["appointment_id"] == appt.id
    assert "reason" in payload

    # Worker notice engagement_event row.
    notices = _engagement_rows(
        db_path, session_id=_SESSION_A,
        category="appointment_auto_missed_notice",
    )
    assert len(notices) == 1
    notice_payload = json.loads(notices[0]["payload_json"])
    assert notice_payload["appointment_id"] == appt.id

    # Outcome record appended (T12.0a integration).
    outcomes = _outcome_rows(db_path, session_id=_SESSION_A)
    advance_outcomes = [
        o for o in outcomes if o["event_type"] == "appointment_auto_advance"
    ]
    assert len(advance_outcomes) == 1


# -------------------- Cycle 3: manual-attended → no action -----------------


def test_already_attended_no_action(db_path: str) -> None:
    """Past appointment that was already marked attended must be left alone."""
    from app.modules.appointments.reconcile import (
        reconcile_session_appointments,
    )

    starts = _NOW - timedelta(hours=24)
    appt = _create_appt(
        session_id=_SESSION_A, starts_at=starts, db_path=db_path,
        status=AppointmentStatus.ATTENDED,
    )
    result = reconcile_session_appointments(
        _SESSION_A, db_path=db_path, now=_NOW,
    )

    assert result.advanced == 0
    refreshed = scheduler.get(appt.id, db_path=db_path)
    assert refreshed.status is AppointmentStatus.ATTENDED
    assert _engagement_rows(
        db_path, session_id=_SESSION_A, category="appointment_auto_advance",
    ) == []


# -------------------- Cycle 4: idempotent --------------------


def test_idempotent_two_runs_no_double_notice(db_path: str) -> None:
    """Re-running after an advance does NOT emit a second notice/audit pair."""
    from app.modules.appointments.reconcile import (
        reconcile_session_appointments,
    )

    starts = _NOW - timedelta(hours=8)
    _create_appt(session_id=_SESSION_A, starts_at=starts, db_path=db_path)

    first = reconcile_session_appointments(
        _SESSION_A, db_path=db_path, now=_NOW,
    )
    second = reconcile_session_appointments(
        _SESSION_A, db_path=db_path, now=_NOW,
    )

    assert first.advanced == 1
    assert second.advanced == 0
    assert len(_engagement_rows(
        db_path, session_id=_SESSION_A, category="appointment_auto_advance",
    )) == 1
    assert len(_engagement_rows(
        db_path, session_id=_SESSION_A,
        category="appointment_auto_missed_notice",
    )) == 1


# -------------------- Cycle 5: stall suppression --------------------


def test_auto_advance_outcome_does_not_reset_stall_clock(
    db_path: str,
) -> None:
    """T12.18 contract: an appointment_auto_advance outcome from reconcile
    must NOT count as worker progress. Worker stalled 10d on dmv stays
    MEDIUM-stalled even after we just auto-missed an appointment now.
    """
    from app.modules.appointments.reconcile import (
        reconcile_session_appointments,
    )

    # Real signal 10 days ago (attended) — sets the stall baseline.
    real_starts = _NOW - timedelta(days=10)
    real_appt = _create_appt(
        session_id=_SESSION_A, starts_at=real_starts, db_path=db_path,
        barrier_link="dmv",
    )
    scheduler.mark_attended(real_appt.id, db_path=db_path)

    # An overdue appointment from earlier today (past the 6h grace window).
    stale_starts = _NOW - timedelta(hours=8)
    _create_appt(
        session_id=_SESSION_A, starts_at=stale_starts, db_path=db_path,
        barrier_link="dmv",
    )

    reconcile_session_appointments(
        _SESSION_A, db_path=db_path, now=_NOW,
    )

    stalled = compute_stall_for_session(
        _SESSION_A, db_path=db_path, now=_NOW,
    )
    # T12.18 filters auto_advance outcomes — stall pin stays at the real
    # 10-day-old attended appointment.
    assert stalled.stall_level is StallLevel.MEDIUM
    assert stalled.days_stalled == 10


# -------------------- Cycle 6: multi-session sweep --------------------


def test_advance_past_bookings_sweeps_all_active_sessions(
    db_path: str,
) -> None:
    """advance_past_bookings iterates every active session it can find."""
    from app.modules.appointments.reconcile import advance_past_bookings

    starts = _NOW - timedelta(hours=8)
    appt_a = _create_appt(
        session_id=_SESSION_A, starts_at=starts, db_path=db_path,
    )
    appt_b = _create_appt(
        session_id=_SESSION_B, starts_at=starts, db_path=db_path,
        barrier_link="childcare",
    )

    result = advance_past_bookings(db_path=db_path, now=_NOW)

    assert result.advanced == 2
    assert scheduler.get(
        appt_a.id, db_path=db_path,
    ).status is AppointmentStatus.MISSED
    assert scheduler.get(
        appt_b.id, db_path=db_path,
    ).status is AppointmentStatus.MISSED


# -------------------- Cycle 7: orchestrator wiring (step 2.5) --------------


def _seed_orchestrator_session(db_path: str) -> None:
    """Seed a session + city tag so collect_active_sessions_for_city finds it."""
    profile = {"first_name": "W", "email": "w@example.com"}
    now_iso = _NOW.isoformat()
    expires = (_NOW + timedelta(days=30)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM sessions WHERE id = ?", (_SESSION_A,))
        conn.execute(
            "INSERT INTO sessions "
            "(id, created_at, barriers, profile, expires_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (_SESSION_A, now_iso, json.dumps(["dmv"]),
             json.dumps(profile), expires),
        )
        conn.execute(
            "INSERT INTO outcomes_records "
            "(session_id, event_type, payload_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (_SESSION_A, "city_tag",
             json.dumps({"city": "montgomery"}), now_iso),
        )
        conn.commit()
    finally:
        conn.close()


def _install_ordering_stubs(
    monkeypatch: pytest.MonkeyPatch, call_order: list[str],
):
    """Patch every step of the nightly pipeline to record its call order."""
    from datetime import date as _date

    import scripts.nightly_digest as nd
    from app.modules.engagement.digest_composer import DigestResult
    from app.modules.engagement.reminder_engine import ReminderDispatchResult
    from app.modules.appointments.reconcile import ReconcileResult
    from app.modules.plan.daily_progress import RetroResult

    def _retro(session_id, for_date, *, db_path):
        call_order.append("retro")
        return RetroResult(
            session_id=session_id,
            for_date=for_date if isinstance(for_date, _date) else _date.today(),
            actions=[], completion_ratio=0.0, summary="stub",
        )

    def _reconcile(session_id, *, db_path, now=None):
        call_order.append("reconcile")
        return ReconcileResult(advanced=0)

    def _compose(session_id, for_date, *, db_path, city=None, now=None):
        call_order.append("compose")
        return DigestResult(
            subject="d", html="<p>x</p>", text="x",
            section_counts={"yesterday": 0, "today": 0, "week": 0, "stall": 0},
        )

    def _send(session_id, to_email, subject, html, text, *, db_path=None, now=None):
        return ReminderDispatchResult(
            success=True, skipped_reason=None,
            category="digest", message_id="m",
        )

    monkeypatch.setattr(nd, "run_nightly_retro", _retro)
    monkeypatch.setattr(nd, "compose_digest", _compose)
    monkeypatch.setattr(nd, "send_digest", _send)
    monkeypatch.setattr(
        nd, "reconcile_session_appointments", _reconcile, raising=False,
    )


def test_nightly_digest_runs_step_2_5_before_compose(
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Orchestrator invokes reconcile (step 2.5) before compose_digest (step 4)."""
    import asyncio

    import scripts.nightly_digest as nd

    _seed_orchestrator_session(db_path)
    call_order: list[str] = []
    _install_ordering_stubs(monkeypatch, call_order)

    asyncio.run(nd.run_nightly_digest(
        cities=["montgomery"], db_path=db_path, now=_NOW,
    ))

    assert "retro" in call_order
    assert "reconcile" in call_order
    assert "compose" in call_order
    assert call_order.index("retro") < call_order.index("reconcile")
    assert call_order.index("reconcile") < call_order.index("compose")
