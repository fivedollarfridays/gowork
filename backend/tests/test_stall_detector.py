"""Tests for engagement.stall_detector (T12.18).

Covers:
- Threshold classification (NONE / SOFT / MEDIUM / HARD)
- Exact boundary days (3, 7, 14)
- No-stall sessions are filtered from scan output
- Auto-advance outcomes filtered (all ages — pragmatic choice, see module docstring)
- Per-barrier tracking with mixed stall levels
- Idempotency same-day
- Engagement status enriched struct with recommendations
- Fresh session today not flagged
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
    JobApplicationStatus,
    StallLevel,
)
from app.modules.engagement.engagement_status import (
    EngagementStatus,
    get_engagement_status,
)
from app.modules.engagement.stall_detector import (
    BarrierStall,
    StalledSession,
    compute_stall_for_session,
    scan_active_sessions,
)
from app.modules.jobs import applications

_SESSION_A = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
_SESSION_B = "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"
_NOW = datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc)


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _isolate_event_bus() -> None:
    events.clear_all_subscribers()
    yield
    events.clear_all_subscribers()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "stall.db")
    runner.apply_pending(path)
    _seed_session(path, _SESSION_A, barriers=["dmv", "childcare"])
    _seed_session(path, _SESSION_B, barriers=["expunction"])
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


def _days_ago(days: int) -> datetime:
    """Return an aware UTC datetime that is `days` days before _NOW."""
    return _NOW - timedelta(days=days)


def _seed_attended_appointment(
    *,
    session_id: str,
    days_ago: int,
    db_path: str,
    barrier_link: str | None = None,
) -> Appointment:
    starts = _days_ago(days_ago)
    appt = Appointment(
        session_id=session_id,
        type=AppointmentType.DMV,
        title="DMV visit",
        starts_at=starts,
        ends_at=starts + timedelta(hours=1),
        location_name="DMV Office",
        barrier_link=barrier_link,
        status=AppointmentStatus.SCHEDULED,
    )
    stored = scheduler.create(session_id, appt, db_path=db_path)
    return scheduler.mark_attended(stored.id, db_path=db_path)


def _seed_application(
    *,
    session_id: str,
    days_ago: int,
    db_path: str,
    url: str = "https://indeed.com/job/x",
):
    applied_on = (_NOW - timedelta(days=days_ago)).date()
    stored = applications.create(
        session_id,
        match_source="indeed",
        match_url=url,
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


def _seed_outcome_row(
    *,
    db_path: str,
    session_id: str,
    event_type: str,
    hours_ago: float,
) -> None:
    """Insert outcomes_records row with an explicit created_at (bypass tracker)."""
    created_at = (_NOW - timedelta(hours=hours_ago)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO outcomes_records "
            "(session_id, event_type, payload_json, created_at, "
            " barriers_cleared_snapshot_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_id, event_type, json.dumps({"city": "montgomery"}),
             created_at, json.dumps([])),
        )
        conn.commit()
    finally:
        conn.close()


# -------------------- Threshold tests --------------------


def test_no_signal_at_all_returns_no_stall_entry(db_path: str) -> None:
    """Fresh session with zero signals is filtered out of scan output."""
    results = scan_active_sessions(db_path=db_path, now=_NOW)
    session_ids = [r.session_id for r in results]
    assert _SESSION_A not in session_ids


def test_soft_stall_after_3_days(db_path: str) -> None:
    _seed_attended_appointment(
        session_id=_SESSION_A, days_ago=3, db_path=db_path,
        barrier_link="dmv",
    )
    stalled = compute_stall_for_session(
        _SESSION_A, db_path=db_path, now=_NOW,
    )
    assert stalled.stall_level == StallLevel.SOFT
    assert stalled.days_stalled == 3


def test_medium_stall_after_7_days(db_path: str) -> None:
    _seed_attended_appointment(
        session_id=_SESSION_A, days_ago=7, db_path=db_path,
        barrier_link="dmv",
    )
    stalled = compute_stall_for_session(
        _SESSION_A, db_path=db_path, now=_NOW,
    )
    assert stalled.stall_level == StallLevel.MEDIUM
    assert stalled.days_stalled == 7


def test_hard_stall_after_14_days(db_path: str) -> None:
    _seed_attended_appointment(
        session_id=_SESSION_A, days_ago=14, db_path=db_path,
        barrier_link="dmv",
    )
    stalled = compute_stall_for_session(
        _SESSION_A, db_path=db_path, now=_NOW,
    )
    assert stalled.stall_level == StallLevel.HARD
    assert stalled.days_stalled == 14


@pytest.mark.parametrize(
    "days_ago,expected",
    [
        (0, StallLevel.NONE),
        (2, StallLevel.NONE),
        (3, StallLevel.SOFT),
        (6, StallLevel.SOFT),
        (7, StallLevel.MEDIUM),
        (13, StallLevel.MEDIUM),
        (14, StallLevel.HARD),
        (30, StallLevel.HARD),
    ],
)
def test_exactly_at_threshold_boundaries(
    db_path: str, days_ago: int, expected: StallLevel,
) -> None:
    _seed_attended_appointment(
        session_id=_SESSION_A, days_ago=days_ago, db_path=db_path,
        barrier_link="dmv",
    )
    stalled = compute_stall_for_session(
        _SESSION_A, db_path=db_path, now=_NOW,
    )
    assert stalled.stall_level == expected


def test_fresh_session_today_not_flagged(db_path: str) -> None:
    """Activity today means no stall; session excluded from scan output."""
    _seed_attended_appointment(
        session_id=_SESSION_A, days_ago=0, db_path=db_path,
        barrier_link="dmv",
    )
    results = scan_active_sessions(db_path=db_path, now=_NOW)
    assert _SESSION_A not in [r.session_id for r in results]


# -------------------- Auto-advance filter tests --------------------


def test_auto_advance_within_48h_does_not_reset_clock(db_path: str) -> None:
    """Auto-advance 24h ago + real signal 10d ago => still MEDIUM."""
    _seed_attended_appointment(
        session_id=_SESSION_A, days_ago=10, db_path=db_path,
        barrier_link="dmv",
    )
    _seed_outcome_row(
        db_path=db_path, session_id=_SESSION_A,
        event_type="appointment_auto_advance", hours_ago=24,
    )
    stalled = compute_stall_for_session(
        _SESSION_A, db_path=db_path, now=_NOW,
    )
    assert stalled.stall_level == StallLevel.MEDIUM
    assert stalled.days_stalled == 10


def test_auto_advance_older_than_48h_still_filtered(db_path: str) -> None:
    """Pragmatic rule: auto-advance NEVER counts regardless of age."""
    _seed_attended_appointment(
        session_id=_SESSION_A, days_ago=10, db_path=db_path,
        barrier_link="dmv",
    )
    _seed_outcome_row(
        db_path=db_path, session_id=_SESSION_A,
        event_type="appointment_auto_advance", hours_ago=60,
    )
    stalled = compute_stall_for_session(
        _SESSION_A, db_path=db_path, now=_NOW,
    )
    assert stalled.stall_level == StallLevel.MEDIUM
    assert stalled.days_stalled == 10


# -------------------- Per-barrier tracking --------------------


def test_multi_barrier_mixed_stalls(db_path: str) -> None:
    """Two barriers each with different last-activity dates -> distinct levels."""
    _seed_attended_appointment(
        session_id=_SESSION_A, days_ago=3, db_path=db_path,
        barrier_link="dmv",
    )
    _seed_attended_appointment(
        session_id=_SESSION_A, days_ago=14, db_path=db_path,
        barrier_link="childcare",
    )
    stalled = compute_stall_for_session(
        _SESSION_A, db_path=db_path, now=_NOW,
    )
    per_barrier = {b.barrier_id: b for b in stalled.stalled_barriers}
    assert per_barrier["dmv"].stall_level == StallLevel.SOFT
    assert per_barrier["childcare"].stall_level == StallLevel.HARD
    # Session-level level is the worst.
    assert stalled.stall_level == StallLevel.HARD
    assert stalled.days_stalled == 14


# -------------------- Idempotency and scan filtering --------------------


def test_idempotent_same_day(db_path: str) -> None:
    _seed_attended_appointment(
        session_id=_SESSION_A, days_ago=7, db_path=db_path,
        barrier_link="dmv",
    )
    first = scan_active_sessions(db_path=db_path, now=_NOW)
    second = scan_active_sessions(db_path=db_path, now=_NOW)
    assert [r.model_dump() for r in first] == [r.model_dump() for r in second]


def test_scan_excludes_no_stall_sessions(db_path: str) -> None:
    """Active session with fresh activity omitted; stalled session included."""
    _seed_attended_appointment(
        session_id=_SESSION_A, days_ago=0, db_path=db_path,
        barrier_link="dmv",
    )
    _seed_attended_appointment(
        session_id=_SESSION_B, days_ago=14, db_path=db_path,
        barrier_link="expunction",
    )
    results = scan_active_sessions(db_path=db_path, now=_NOW)
    ids = [r.session_id for r in results]
    assert _SESSION_A not in ids
    assert _SESSION_B in ids


# -------------------- Signal coverage --------------------


def test_application_filed_counts_as_progress(db_path: str) -> None:
    """Application filed 2 days ago => NONE even with no other signal."""
    _seed_application(
        session_id=_SESSION_A, days_ago=2, db_path=db_path,
    )
    stalled = compute_stall_for_session(
        _SESSION_A, db_path=db_path, now=_NOW,
    )
    assert stalled.stall_level == StallLevel.NONE


def test_non_auto_advance_outcome_counts_as_progress(db_path: str) -> None:
    """plan_followed outcome 2 days ago => NONE."""
    _seed_outcome_row(
        db_path=db_path, session_id=_SESSION_A,
        event_type="plan_followed", hours_ago=48,
    )
    stalled = compute_stall_for_session(
        _SESSION_A, db_path=db_path, now=_NOW,
    )
    assert stalled.stall_level == StallLevel.NONE


# -------------------- Engagement status --------------------


def test_get_engagement_status_returns_recommendations(db_path: str) -> None:
    _seed_attended_appointment(
        session_id=_SESSION_A, days_ago=7, db_path=db_path,
        barrier_link="dmv",
    )
    status = get_engagement_status(
        _SESSION_A, db_path=db_path, now=_NOW,
    )
    assert isinstance(status, EngagementStatus)
    assert status.stall_level == StallLevel.MEDIUM
    assert status.days_since_last_action == 7
    # Recommendations is a list of dicts with 'type'/'message'/'urgency'.
    assert isinstance(status.recommendations, list)
    assert len(status.recommendations) >= 1
    rec = status.recommendations[0]
    assert {"type", "message", "urgency"}.issubset(set(rec.keys()))


def test_get_engagement_status_none_when_fresh(db_path: str) -> None:
    _seed_attended_appointment(
        session_id=_SESSION_A, days_ago=0, db_path=db_path,
        barrier_link="dmv",
    )
    status = get_engagement_status(
        _SESSION_A, db_path=db_path, now=_NOW,
    )
    assert status.stall_level == StallLevel.NONE
    assert status.days_since_last_action == 0
    # A fresh session still surfaces an "all clear" / keep-going note.
    assert isinstance(status.recommendations, list)


# -------------------- Returned model shape --------------------


def test_stalled_session_model_shape(db_path: str) -> None:
    _seed_attended_appointment(
        session_id=_SESSION_A, days_ago=7, db_path=db_path,
        barrier_link="dmv",
    )
    stalled = compute_stall_for_session(
        _SESSION_A, db_path=db_path, now=_NOW,
    )
    assert isinstance(stalled, StalledSession)
    assert all(isinstance(b, BarrierStall) for b in stalled.stalled_barriers)
