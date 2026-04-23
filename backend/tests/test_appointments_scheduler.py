"""Tests for appointments scheduler + outcomes listener (T12.7).

Covers:
- create() inserts + emits `appointment.created`
- mark_attended / mark_missed / cancel validate transitions, emit events
- reschedule preserves old starts_at in notes, validates transition
- overlap detection warns but never raises
- list_upcoming filters by date window
- list_by_session returns chronological order
- outcomes listener writes an append-only record per event
- the full ALLOWED transition matrix (parametric)
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core import events
from app.core.migrations import runner
from app.modules.appointments import scheduler
from app.modules.appointments.outcomes_listener import (
    register_outcomes_listener,
)
from app.modules.appointments.status_transitions import (
    ALLOWED,
    InvalidStatusTransition,
    check_transition,
)
from app.modules.appointments.types import Appointment
from app.modules.common.temporal_types import (
    AppointmentStatus,
    AppointmentType,
)
from app.modules.outcomes.tracker import OutcomeTracker

_SESSION = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
_SESSION_B = "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _isolate_event_bus() -> None:
    events.clear_all_subscribers()
    yield
    events.clear_all_subscribers()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "appt.db")
    runner.apply_pending(path)
    _seed_sessions(path, [_SESSION, _SESSION_B])
    return path


def _seed_sessions(path: str, ids: list[str]) -> None:
    conn = sqlite3.connect(path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        for sid in ids:
            conn.execute(
                "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                "VALUES (?, ?, ?, ?)",
                (sid, now, "[]", now),
            )
        conn.commit()
    finally:
        conn.close()


def _appt(
    *,
    session_id: str = _SESSION,
    starts_offset_h: int = 24,
    duration_min: int = 60,
    status: AppointmentStatus = AppointmentStatus.SCHEDULED,
    title: str = "DMV visit",
    barrier_link: str | None = "dmv",
    notes: str | None = None,
) -> Appointment:
    starts = datetime.now(timezone.utc) + timedelta(hours=starts_offset_h)
    return Appointment(
        session_id=session_id,
        type=AppointmentType.DMV,
        title=title,
        starts_at=starts,
        ends_at=starts + timedelta(minutes=duration_min),
        location_name="DMV Office",
        status=status,
        barrier_link=barrier_link,
        notes=notes,
    )


# -------------------- create + events --------------------


def test_create_inserts_and_emits_created_event(db_path: str) -> None:
    captured: list[dict] = []
    events.subscribe("appointment.created", captured.append)

    stored = scheduler.create(_SESSION, _appt(), db_path=db_path)

    assert stored.id is not None
    fetched = scheduler.get(stored.id, db_path=db_path)
    assert fetched is not None
    assert fetched.title == "DMV visit"
    assert captured and captured[0]["id"] == stored.id


def test_create_rejects_mismatched_session_id(db_path: str) -> None:
    with pytest.raises(ValueError, match="session_id"):
        scheduler.create(_SESSION_B, _appt(), db_path=db_path)


# -------------------- mark_attended / missed / cancel --------------------


def test_mark_attended_from_scheduled_succeeds(db_path: str) -> None:
    stored = scheduler.create(_SESSION, _appt(), db_path=db_path)
    captured: list[dict] = []
    events.subscribe("appointment.attended", captured.append)

    updated = scheduler.mark_attended(stored.id, db_path=db_path)

    assert updated.status == AppointmentStatus.ATTENDED
    assert captured and captured[0]["status"] == "attended"


def test_mark_attended_from_cancelled_raises(db_path: str) -> None:
    stored = scheduler.create(_SESSION, _appt(), db_path=db_path)
    scheduler.cancel(stored.id, db_path=db_path)

    with pytest.raises(InvalidStatusTransition):
        scheduler.mark_attended(stored.id, db_path=db_path)


def test_mark_missed_only_valid_from_scheduled(db_path: str) -> None:
    stored = scheduler.create(_SESSION, _appt(), db_path=db_path)
    scheduler.mark_attended(stored.id, db_path=db_path)

    with pytest.raises(InvalidStatusTransition):
        scheduler.mark_missed(stored.id, db_path=db_path)


def test_cancel_from_attended_raises(db_path: str) -> None:
    stored = scheduler.create(_SESSION, _appt(), db_path=db_path)
    scheduler.mark_attended(stored.id, db_path=db_path)

    with pytest.raises(InvalidStatusTransition):
        scheduler.cancel(stored.id, db_path=db_path)


# -------------------- reschedule --------------------


def test_reschedule_preserves_old_starts_at_in_notes(db_path: str) -> None:
    stored = scheduler.create(_SESSION, _appt(starts_offset_h=24), db_path=db_path)
    old_iso = stored.starts_at.isoformat()
    new_start = stored.starts_at + timedelta(days=2)
    new_end = new_start + timedelta(hours=1)
    captured: list[dict] = []
    events.subscribe("appointment.rescheduled", captured.append)

    updated = scheduler.reschedule(
        stored.id, new_start, new_end, db_path=db_path,
    )

    assert updated.status == AppointmentStatus.RESCHEDULED
    assert updated.starts_at == new_start
    assert old_iso in (updated.notes or "")
    assert captured and captured[0]["id"] == stored.id


# -------------------- overlap warning --------------------


def test_overlap_logs_warning_not_raise(
    db_path: str, caplog: pytest.LogCaptureFixture,
) -> None:
    first = scheduler.create(_SESSION, _appt(starts_offset_h=24), db_path=db_path)
    overlapping = _appt(starts_offset_h=24)  # same window as first

    with caplog.at_level(
        logging.WARNING, logger="app.modules.appointments.scheduler",
    ):
        second = scheduler.create(_SESSION, overlapping, db_path=db_path)

    assert second.id is not None and second.id != first.id
    assert "Overlapping appointments" in caplog.text


# -------------------- list helpers --------------------


def test_list_upcoming_filters_by_date_range(db_path: str) -> None:
    scheduler.create(_SESSION, _appt(starts_offset_h=12), db_path=db_path)  # in
    scheduler.create(_SESSION, _appt(starts_offset_h=24 * 10), db_path=db_path)  # out

    upcoming = scheduler.list_upcoming(_SESSION, days=2, db_path=db_path)

    assert len(upcoming) == 1


def test_list_by_session_returns_chronological(db_path: str) -> None:
    later = scheduler.create(_SESSION, _appt(starts_offset_h=48), db_path=db_path)
    earlier = scheduler.create(_SESSION, _appt(starts_offset_h=12), db_path=db_path)

    ordered = scheduler.list_by_session(_SESSION, db_path=db_path)
    ids = [a.id for a in ordered]

    assert ids == [earlier.id, later.id]


# -------------------- transition matrix (parametric) --------------------


_ALL_STATUSES = list(AppointmentStatus)


@pytest.mark.parametrize("current", _ALL_STATUSES)
@pytest.mark.parametrize("target", _ALL_STATUSES)
def test_all_status_transitions_matrix_parametric(
    current: AppointmentStatus, target: AppointmentStatus,
) -> None:
    if target in ALLOWED[current]:
        check_transition(current, target)  # must not raise
    else:
        with pytest.raises(InvalidStatusTransition):
            check_transition(current, target)


# -------------------- outcomes listener --------------------


def test_outcomes_listener_writes_on_attended(db_path: str) -> None:
    register_outcomes_listener(db_path)
    stored = scheduler.create(_SESSION, _appt(), db_path=db_path)
    scheduler.mark_attended(stored.id, db_path=db_path)

    records = OutcomeTracker(db_path).list_by_session(_SESSION)
    signal_types = [r.signal_type for r in records]

    assert "appointment_created" in signal_types
    assert "appointment_attended" in signal_types


def test_outcomes_listener_writes_on_missed(db_path: str) -> None:
    register_outcomes_listener(db_path)
    stored = scheduler.create(_SESSION, _appt(), db_path=db_path)
    scheduler.mark_missed(stored.id, db_path=db_path)

    records = OutcomeTracker(db_path).list_by_session(_SESSION)
    missed = [r for r in records if r.signal_type == "appointment_missed"]

    assert len(missed) == 1
    # barrier_link="dmv" should flow into resource_ratings as False (ineffective).
    assert missed[0].resource_ratings.get("dmv") is False
