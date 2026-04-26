"""Tests for plan.evidence_collector.collect_evidence (T12.23).

Covers:
- Empty bundle structure when no signals
- Appointments attended / missed filtered by range
- Applications filed (APPLIED status) filtered by range
- Applications progressed (outcome-derived, APPLIED -> INTERVIEW and up)
- Outcomes logged within range
- Inclusive range boundaries (start / end / before / after / single-day)
- Multi-session isolation
- Overlapping ranges consistency
- Cross-city scope (implicit via session_id)
- Checklist is empty-list placeholder (no table yet)
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import pytest

from app.core import events
from app.core.migrations import runner
from tests._fake_clock import freeze_time as _freeze_time


@pytest.fixture
def freeze_wednesday():
    """Freeze clock to Wednesday 2026-04-22 12:00 UTC.

    Avoids two flake classes:
      1. local-time `date.today()` drifting from UTC `datetime.now()`
         around midnight (this test compares both)
      2. running on a Sunday triggering the weekly-review branch in
         tested orchestrator code
    """
    with _freeze_time("2026-04-22T12:00:00+00:00"):
        yield
from app.modules.appointments import scheduler
from app.modules.appointments.types import Appointment
from app.modules.common.temporal_types import (
    AppointmentStatus,
    AppointmentType,
    JobApplicationStatus,
)
from app.modules.jobs import applications
from app.modules.jobs.outcomes_listener import register_jobs_outcomes_listener
from app.modules.outcomes.tracker import OutcomeTracker
from app.modules.outcomes.types import OutcomeRecord
from app.modules.plan.evidence_collector import EvidenceBundle, collect_evidence

_SESSION_A = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
_SESSION_B = "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _isolate_event_bus() -> None:
    events.clear_all_subscribers()
    yield
    events.clear_all_subscribers()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "evidence.db")
    runner.apply_pending(path)
    _seed_sessions(path, [_SESSION_A, _SESSION_B])
    return path


def _seed_sessions(path: str, ids: list[str]) -> None:
    conn = sqlite3.connect(path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        for sid in ids:
            conn.execute(
                "INSERT INTO sessions (id, created_at, barriers, profile, expires_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (sid, now, "[]", "{}", now),
            )
        conn.commit()
    finally:
        conn.close()


# -------------------- Helpers --------------------


def _midday(d: date) -> datetime:
    """12:00 UTC on date d — easy to reason about without TZ edge cases."""
    return datetime.combine(d, time(12, 0, tzinfo=timezone.utc))


def _make_appointment(
    *,
    session_id: str,
    starts_at: datetime,
    status: AppointmentStatus,
    db_path: str,
) -> Appointment:
    """Create + transition an appointment to the requested terminal status."""
    appt = Appointment(
        session_id=session_id,
        type=AppointmentType.DMV,
        title="DMV visit",
        starts_at=starts_at,
        ends_at=starts_at + timedelta(hours=1),
        location_name="DMV Office",
        status=AppointmentStatus.SCHEDULED,
    )
    stored = scheduler.create(session_id, appt, db_path=db_path)
    if status is AppointmentStatus.ATTENDED:
        return scheduler.mark_attended(stored.id, db_path=db_path)
    if status is AppointmentStatus.MISSED:
        return scheduler.mark_missed(stored.id, db_path=db_path)
    return stored


def _make_applied(
    *,
    session_id: str,
    applied_on: date,
    db_path: str,
    match_url: str = "https://indeed.com/job/abc",
):
    """Create a job app and transition DRAFT -> APPLIED with the given date."""
    stored = applications.create(
        session_id,
        match_source="indeed",
        match_url=match_url,
        company="Acme",
        role="Tech",
        db_path=db_path,
    )
    return applications.update_status(
        stored.id,
        JobApplicationStatus.APPLIED,
        outcome_date=applied_on,
        db_path=db_path,
    )


# -------------------- Tests --------------------


def test_empty_bundle_when_no_signals(db_path: str) -> None:
    start = date(2026, 4, 20)
    end = date(2026, 4, 26)
    bundle = collect_evidence(
        _SESSION_A, start=start, end=end, db_path=db_path,
    )
    assert isinstance(bundle, EvidenceBundle)
    assert bundle.session_id == _SESSION_A
    assert bundle.date_range_start == start
    assert bundle.date_range_end == end
    assert bundle.checklist_items_completed == []
    assert bundle.appointments_attended == []
    assert bundle.appointments_missed == []
    assert bundle.applications_filed == []
    assert bundle.applications_progressed == []
    assert bundle.outcomes_logged == []


def test_appointments_attended_in_range(db_path: str) -> None:
    start = date(2026, 4, 20)
    end = date(2026, 4, 26)
    appt = _make_appointment(
        session_id=_SESSION_A,
        starts_at=_midday(date(2026, 4, 22)),
        status=AppointmentStatus.ATTENDED,
        db_path=db_path,
    )
    bundle = collect_evidence(
        _SESSION_A, start=start, end=end, db_path=db_path,
    )
    assert [a.id for a in bundle.appointments_attended] == [appt.id]
    assert bundle.appointments_missed == []


def test_appointments_missed_in_range(db_path: str) -> None:
    start = date(2026, 4, 20)
    end = date(2026, 4, 26)
    appt = _make_appointment(
        session_id=_SESSION_A,
        starts_at=_midday(date(2026, 4, 23)),
        status=AppointmentStatus.MISSED,
        db_path=db_path,
    )
    bundle = collect_evidence(
        _SESSION_A, start=start, end=end, db_path=db_path,
    )
    assert [a.id for a in bundle.appointments_missed] == [appt.id]
    assert bundle.appointments_attended == []


def test_range_inclusive_on_start_day(db_path: str) -> None:
    start = date(2026, 4, 20)
    end = date(2026, 4, 26)
    appt = _make_appointment(
        session_id=_SESSION_A,
        starts_at=_midday(start),
        status=AppointmentStatus.ATTENDED,
        db_path=db_path,
    )
    bundle = collect_evidence(
        _SESSION_A, start=start, end=end, db_path=db_path,
    )
    assert [a.id for a in bundle.appointments_attended] == [appt.id]


def test_range_inclusive_on_end_day(db_path: str) -> None:
    start = date(2026, 4, 20)
    end = date(2026, 4, 26)
    # 23:30 on the end day — well past noon but still on end date.
    late_on_end = datetime.combine(end, time(23, 30, tzinfo=timezone.utc))
    appt = _make_appointment(
        session_id=_SESSION_A,
        starts_at=late_on_end,
        status=AppointmentStatus.ATTENDED,
        db_path=db_path,
    )
    bundle = collect_evidence(
        _SESSION_A, start=start, end=end, db_path=db_path,
    )
    assert [a.id for a in bundle.appointments_attended] == [appt.id]


def test_range_exclusive_before_start(db_path: str) -> None:
    start = date(2026, 4, 20)
    end = date(2026, 4, 26)
    _make_appointment(
        session_id=_SESSION_A,
        starts_at=_midday(start - timedelta(days=1)),
        status=AppointmentStatus.ATTENDED,
        db_path=db_path,
    )
    bundle = collect_evidence(
        _SESSION_A, start=start, end=end, db_path=db_path,
    )
    assert bundle.appointments_attended == []


def test_range_exclusive_after_end(db_path: str) -> None:
    start = date(2026, 4, 20)
    end = date(2026, 4, 26)
    _make_appointment(
        session_id=_SESSION_A,
        starts_at=_midday(end + timedelta(days=1)),
        status=AppointmentStatus.ATTENDED,
        db_path=db_path,
    )
    bundle = collect_evidence(
        _SESSION_A, start=start, end=end, db_path=db_path,
    )
    assert bundle.appointments_attended == []


def test_applications_filed_in_range(db_path: str) -> None:
    start = date(2026, 4, 20)
    end = date(2026, 4, 26)
    filed = _make_applied(
        session_id=_SESSION_A,
        applied_on=date(2026, 4, 22),
        db_path=db_path,
    )
    bundle = collect_evidence(
        _SESSION_A, start=start, end=end, db_path=db_path,
    )
    assert [a.id for a in bundle.applications_filed] == [filed.id]


def test_applications_filed_excludes_out_of_range(db_path: str) -> None:
    start = date(2026, 4, 20)
    end = date(2026, 4, 26)
    _make_applied(
        session_id=_SESSION_A,
        applied_on=date(2026, 4, 10),
        db_path=db_path,
    )
    bundle = collect_evidence(
        _SESSION_A, start=start, end=end, db_path=db_path,
    )
    assert bundle.applications_filed == []


def test_applications_progressed_in_range(db_path: str) -> None:
    # The outcomes listener has to be registered for progression events
    # to land in outcomes_records.
    register_jobs_outcomes_listener(db_path)
    start = date(2026, 4, 20)
    end = date(2026, 4, 26)
    filed = _make_applied(
        session_id=_SESSION_A,
        applied_on=date(2026, 4, 21),
        db_path=db_path,
    )
    applications.update_status(
        filed.id,
        JobApplicationStatus.INTERVIEW,
        db_path=db_path,
    )
    bundle = collect_evidence(
        _SESSION_A, start=start, end=end, db_path=db_path,
    )
    assert [a.id for a in bundle.applications_progressed] == [filed.id]


def test_applications_progressed_empty_when_only_filed(db_path: str) -> None:
    """APPLIED-only activity in the window must NOT count as progressed."""
    register_jobs_outcomes_listener(db_path)
    start = date(2026, 4, 20)
    end = date(2026, 4, 26)
    _make_applied(
        session_id=_SESSION_A,
        applied_on=date(2026, 4, 21),
        db_path=db_path,
    )
    bundle = collect_evidence(
        _SESSION_A, start=start, end=end, db_path=db_path,
    )
    assert bundle.applications_progressed == []


@pytest.mark.usefixtures("freeze_wednesday")
def test_outcomes_logged_in_range(db_path: str) -> None:
    tracker = OutcomeTracker(db_path)
    tracker.record_outcome(OutcomeRecord(
        session_id=_SESSION_A,
        signal_type="plan_followed",
        city="montgomery",
    ))
    start = date.today()
    end = start
    bundle = collect_evidence(
        _SESSION_A, start=start, end=end, db_path=db_path,
    )
    # Exactly one outcome with the signal type we just recorded.
    assert len(bundle.outcomes_logged) == 1
    assert bundle.outcomes_logged[0].signal_type == "plan_followed"


def test_single_day_range_returns_that_days_signals(db_path: str) -> None:
    day = date(2026, 4, 22)
    appt = _make_appointment(
        session_id=_SESSION_A,
        starts_at=_midday(day),
        status=AppointmentStatus.ATTENDED,
        db_path=db_path,
    )
    # Signal one day before — must not appear.
    _make_appointment(
        session_id=_SESSION_A,
        starts_at=_midday(day - timedelta(days=1)),
        status=AppointmentStatus.MISSED,
        db_path=db_path,
    )
    bundle = collect_evidence(
        _SESSION_A, start=day, end=day, db_path=db_path,
    )
    assert [a.id for a in bundle.appointments_attended] == [appt.id]
    assert bundle.appointments_missed == []


def test_multi_session_isolation(db_path: str) -> None:
    start = date(2026, 4, 20)
    end = date(2026, 4, 26)
    a_appt = _make_appointment(
        session_id=_SESSION_A,
        starts_at=_midday(date(2026, 4, 22)),
        status=AppointmentStatus.ATTENDED,
        db_path=db_path,
    )
    _make_appointment(
        session_id=_SESSION_B,
        starts_at=_midday(date(2026, 4, 22)),
        status=AppointmentStatus.MISSED,
        db_path=db_path,
    )
    bundle_a = collect_evidence(
        _SESSION_A, start=start, end=end, db_path=db_path,
    )
    bundle_b = collect_evidence(
        _SESSION_B, start=start, end=end, db_path=db_path,
    )
    assert [a.id for a in bundle_a.appointments_attended] == [a_appt.id]
    assert bundle_a.appointments_missed == []
    assert bundle_b.appointments_attended == []
    assert len(bundle_b.appointments_missed) == 1


def test_overlapping_ranges_consistency(db_path: str) -> None:
    """[d1..d5] and [d3..d7] both include signals on d3, d4, d5."""
    d1 = date(2026, 4, 20)
    d3 = date(2026, 4, 22)
    d5 = date(2026, 4, 24)
    d7 = date(2026, 4, 26)

    middle_appt = _make_appointment(
        session_id=_SESSION_A,
        starts_at=_midday(d3),
        status=AppointmentStatus.ATTENDED,
        db_path=db_path,
    )

    bundle_early = collect_evidence(
        _SESSION_A, start=d1, end=d5, db_path=db_path,
    )
    bundle_late = collect_evidence(
        _SESSION_A, start=d3, end=d7, db_path=db_path,
    )
    assert [a.id for a in bundle_early.appointments_attended] == [middle_appt.id]
    assert [a.id for a in bundle_late.appointments_attended] == [middle_appt.id]


def test_cross_city_scope_implicit_via_session_id(db_path: str) -> None:
    """Each session's bundle only carries its own data.

    City is not an explicit param; scoping falls out of session_id since
    sessions are FK-bound to their city via the sessions table.
    """
    start = date(2026, 4, 20)
    end = date(2026, 4, 26)
    a_appt = _make_appointment(
        session_id=_SESSION_A,
        starts_at=_midday(date(2026, 4, 22)),
        status=AppointmentStatus.ATTENDED,
        db_path=db_path,
    )
    b_appt = _make_appointment(
        session_id=_SESSION_B,
        starts_at=_midday(date(2026, 4, 23)),
        status=AppointmentStatus.ATTENDED,
        db_path=db_path,
    )
    a_ids = [
        x.id for x in collect_evidence(
            _SESSION_A, start=start, end=end, db_path=db_path,
        ).appointments_attended
    ]
    b_ids = [
        x.id for x in collect_evidence(
            _SESSION_B, start=start, end=end, db_path=db_path,
        ).appointments_attended
    ]
    assert a_ids == [a_appt.id]
    assert b_ids == [b_appt.id]


def test_checklist_empty_list_placeholder(db_path: str) -> None:
    """No structured checklist table yet — bundle carries empty list."""
    bundle = collect_evidence(
        _SESSION_A,
        start=date(2026, 4, 20),
        end=date(2026, 4, 26),
        db_path=db_path,
    )
    assert bundle.checklist_items_completed == []
