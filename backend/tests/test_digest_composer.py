"""Tests for engagement.digest_composer.compose_digest (T12.20).

Covers:
- Subject line + all-empty minimal digest
- Worker first-name resolution (profile.first_name, profile.name, fallback)
- Yesterday section — attended appointments, filed applications, barriers cleared
- Today section — upcoming appointments with prep hints, dedupe, carryover
- This-week section — empty for S12a (fair-chance feed + recert deferred)
- Stall alerts — HARD/SOFT/NONE levels
- HTML escaping of worker-supplied dynamic values
- Accurate section_counts for observability
- Snapshot tests for all-empty and fully-populated cases
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, time, timedelta, timezone
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
)
from app.modules.engagement.digest_composer import DigestResult, compose_digest
from app.modules.jobs import applications

_SESSION_A = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
_FOR_DATE = date(2026, 4, 23)
# Freeze "now" so upcoming-today filtering is deterministic: 08:00 UTC
# on _FOR_DATE lets us schedule appointments later in the day that
# still fall inside `list_upcoming(days=1)`'s [now, now+1d] window.
_NOW_FROZEN = datetime(2026, 4, 23, 8, 0, tzinfo=timezone.utc)


# -------------------- Fixtures --------------------


@pytest.fixture(autouse=True)
def _isolate_event_bus() -> None:
    events.clear_all_subscribers()
    yield
    events.clear_all_subscribers()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "digest.db")
    runner.apply_pending(path)
    _seed_session(path, _SESSION_A, profile={})
    return path


def _seed_session(
    path: str,
    sid: str,
    *,
    profile: dict | None,
    barriers: list[str] | None = None,
) -> None:
    conn = sqlite3.connect(path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        conn.execute("DELETE FROM sessions WHERE id = ?", (sid,))
        conn.execute(
            "INSERT INTO sessions "
            "(id, created_at, barriers, profile, expires_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                sid,
                now,
                json.dumps(barriers or []),
                json.dumps(profile) if profile is not None else None,
                expires,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _at(d: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(
        d, time(hour, minute, tzinfo=timezone.utc),
    )


def _create_appointment(
    *,
    db_path: str,
    starts_at: datetime,
    title: str = "DMV visit",
    appt_type: AppointmentType = AppointmentType.DMV,
    location_name: str = "DMV Office",
) -> Appointment:
    appt = Appointment(
        session_id=_SESSION_A,
        type=appt_type,
        title=title,
        starts_at=starts_at,
        ends_at=starts_at + timedelta(hours=1),
        location_name=location_name,
        status=AppointmentStatus.SCHEDULED,
    )
    return scheduler.create(_SESSION_A, appt, db_path=db_path)


def _attended_yesterday(*, db_path: str, title: str = "DMV visit") -> Appointment:
    appt = _create_appointment(
        db_path=db_path,
        starts_at=_at(_FOR_DATE - timedelta(days=1), 14),
        title=title,
    )
    return scheduler.mark_attended(appt.id, db_path=db_path)


def _missed_yesterday(*, db_path: str, title: str = "DMV visit") -> Appointment:
    appt = _create_appointment(
        db_path=db_path,
        starts_at=_at(_FOR_DATE - timedelta(days=1), 10),
        title=title,
    )
    return scheduler.mark_missed(appt.id, db_path=db_path)


def _filed_application(
    *,
    db_path: str,
    company: str = "Acme",
    role: str = "Tech",
    match_url: str = "https://indeed.com/job/abc",
) -> None:
    stored = applications.create(
        _SESSION_A,
        match_source="indeed",
        match_url=match_url,
        company=company,
        role=role,
        db_path=db_path,
    )
    applications.update_status(
        stored.id,
        JobApplicationStatus.APPLIED,
        outcome_date=_FOR_DATE - timedelta(days=1),
        db_path=db_path,
    )


def _seed_barrier_cleared(*, db_path: str, barrier: str) -> None:
    """Insert an outcomes_records row with event_type='barrier.cleared'."""
    conn = sqlite3.connect(db_path)
    try:
        created = _at(_FOR_DATE - timedelta(days=1), 12).isoformat()
        conn.execute(
            "INSERT INTO outcomes_records "
            "(session_id, event_type, payload_json, created_at, "
            " barriers_cleared_snapshot_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                _SESSION_A,
                "barrier.cleared",
                json.dumps({"barrier_id": barrier, "city": "montgomery"}),
                created,
                json.dumps([barrier]),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _seed_attended_signal_n_days_ago(*, db_path: str, days: int) -> None:
    """Seed an attended appointment N days ago (for stall-level control)."""
    appt = _create_appointment(
        db_path=db_path,
        starts_at=_NOW_FROZEN - timedelta(days=days),
        title=f"Legacy appt {days}d ago",
    )
    scheduler.mark_attended(appt.id, db_path=db_path)


# -------------------- Cycle 1: subject + first-name resolution --------------------


def test_all_empty_sections_produce_minimal_digest(db_path: str) -> None:
    result = compose_digest(
        _SESSION_A, _FOR_DATE, db_path=db_path, now=_NOW_FROZEN,
    )
    assert isinstance(result, DigestResult)
    assert result.subject.startswith("[MontGoWork] Your daily digest")
    assert "Thursday, Apr 23" in result.subject
    assert "nothing new today" in result.html.lower()
    assert "nothing new today" in result.text.lower()
    assert result.section_counts == {
        "yesterday": 0, "today": 0, "week": 0, "stall": 0,
    }


def test_first_name_from_profile_first_name(db_path: str) -> None:
    _seed_session(db_path, _SESSION_A, profile={"first_name": "Alice"})
    result = compose_digest(
        _SESSION_A, _FOR_DATE, db_path=db_path, now=_NOW_FROZEN,
    )
    assert "Alice" in result.html
    assert "Alice" in result.text


def test_first_name_falls_back_to_name_first_word(db_path: str) -> None:
    _seed_session(db_path, _SESSION_A, profile={"name": "Bob Smith"})
    result = compose_digest(
        _SESSION_A, _FOR_DATE, db_path=db_path, now=_NOW_FROZEN,
    )
    assert "Bob" in result.html
    # must NOT render "Smith" standalone as the greeting token
    assert "Hi Bob" in result.text or "Hello Bob" in result.text


def test_first_name_falls_back_to_friend_when_missing(db_path: str) -> None:
    _seed_session(db_path, _SESSION_A, profile={})
    result = compose_digest(
        _SESSION_A, _FOR_DATE, db_path=db_path, now=_NOW_FROZEN,
    )
    assert "friend" in result.html.lower()
    assert "friend" in result.text.lower()


# -------------------- Cycle 2: yesterday section --------------------


def test_yesterday_attended_appointment_renders(db_path: str) -> None:
    _attended_yesterday(db_path=db_path, title="DMV license renewal")
    result = compose_digest(
        _SESSION_A, _FOR_DATE, db_path=db_path, now=_NOW_FROZEN,
    )
    assert "Yesterday" in result.html
    assert "DMV license renewal" in result.html
    assert "1 appointment attended" in result.html
    assert "1 appointment attended" in result.text
    assert result.section_counts["yesterday"] == 1


def test_yesterday_filed_application_renders(db_path: str) -> None:
    _filed_application(db_path=db_path, company="Acme Logistics", role="Driver")
    result = compose_digest(
        _SESSION_A, _FOR_DATE, db_path=db_path, now=_NOW_FROZEN,
    )
    assert "Acme Logistics" in result.html
    assert "Driver" in result.html
    # HTML uses em-dash; also verify in text variant
    assert "Acme Logistics" in result.text
    assert "Driver" in result.text
    assert result.section_counts["yesterday"] == 1


def test_yesterday_barrier_cleared_renders(db_path: str) -> None:
    _seed_barrier_cleared(db_path=db_path, barrier="dmv")
    result = compose_digest(
        _SESSION_A, _FOR_DATE, db_path=db_path, now=_NOW_FROZEN,
    )
    assert "cleared" in result.html.lower()
    assert "dmv" in result.html
    assert result.section_counts["yesterday"] == 1


# -------------------- Cycle 3: today section --------------------


def test_today_upcoming_appointment_renders(db_path: str) -> None:
    _create_appointment(
        db_path=db_path,
        starts_at=_at(_FOR_DATE, 15),
        title="Career center orientation",
        appt_type=AppointmentType.CAREER_CENTER,
        location_name="Downtown Center",
    )
    result = compose_digest(
        _SESSION_A, _FOR_DATE, db_path=db_path, now=_NOW_FROZEN,
    )
    assert "Today" in result.html
    assert "Career center orientation" in result.html
    assert "Downtown Center" in result.html
    # prep hint surfaces
    assert "30 minutes before" in result.html
    assert "30 minutes before" in result.text
    assert result.section_counts["today"] == 1


def test_dedupe_by_time_slot_collapses_same_time(db_path: str) -> None:
    """Two appts sharing start/end collapse to one rendered entry."""
    starts = _at(_FOR_DATE, 14)
    # Lower-priority: OTHER type
    _create_appointment(
        db_path=db_path,
        starts_at=starts,
        title="Generic fallback",
        appt_type=AppointmentType.OTHER,
        location_name="Somewhere",
    )
    # Higher-priority: JOB_INTERVIEW
    _create_appointment(
        db_path=db_path,
        starts_at=starts,
        title="Interview with Acme",
        appt_type=AppointmentType.JOB_INTERVIEW,
        location_name="Acme HQ",
    )
    result = compose_digest(
        _SESSION_A, _FOR_DATE, db_path=db_path, now=_NOW_FROZEN,
    )
    # Winner (higher priority) survives
    assert "Interview with Acme" in result.html
    # Loser is dropped
    assert "Generic fallback" not in result.html
    assert result.section_counts["today"] == 1


def test_carryover_renders_yesterday_undone(db_path: str) -> None:
    _missed_yesterday(db_path=db_path, title="Follow up with childcare")
    result = compose_digest(
        _SESSION_A, _FOR_DATE, db_path=db_path, now=_NOW_FROZEN,
    )
    assert "Today" in result.html
    assert "Carried over" in result.html
    assert "Follow up with childcare" in result.html
    assert "Carried over" in result.text


# -------------------- Cycle 4: this-week section --------------------


def test_week_section_populates_for_future_appointment(db_path: str) -> None:
    """Appt 3 days ahead surfaces in week section (other sub-sections TBD)."""
    _create_appointment(
        db_path=db_path,
        starts_at=_at(_FOR_DATE + timedelta(days=3), 10),
        title="Court hearing",
        appt_type=AppointmentType.COURT_HEARING,
        location_name="District Court",
    )
    result = compose_digest(
        _SESSION_A, _FOR_DATE, db_path=db_path, now=_NOW_FROZEN,
    )
    assert "This week" in result.html
    assert "Court hearing" in result.html
    assert result.section_counts["week"] == 1


def test_week_section_empty_for_s12a(db_path: str) -> None:
    """No upcoming future appts + no fair-chance feed = week section omitted."""
    result = compose_digest(
        _SESSION_A, _FOR_DATE, db_path=db_path, now=_NOW_FROZEN,
    )
    # section omitted from html + text, and count is 0
    assert "This week" not in result.html
    assert "This week" not in result.text
    assert result.section_counts["week"] == 0


# -------------------- Cycle 5: stall alerts --------------------


def test_stall_alert_hard_renders_advisor_cta(db_path: str) -> None:
    # Seed attended 14+ days ago to trigger HARD stall
    _seed_attended_signal_n_days_ago(db_path=db_path, days=14)
    result = compose_digest(
        _SESSION_A, _FOR_DATE, db_path=db_path, now=_NOW_FROZEN,
    )
    assert "navigator" in result.html.lower()
    assert "navigator" in result.text.lower()
    assert result.section_counts["stall"] == 1


def test_stall_alert_none_omits_section(db_path: str) -> None:
    # No stall signal at all: level = NONE
    result = compose_digest(
        _SESSION_A, _FOR_DATE, db_path=db_path, now=_NOW_FROZEN,
    )
    assert "navigator" not in result.html.lower()
    assert "check-in" not in result.html.lower()
    assert result.section_counts["stall"] == 0


# -------------------- Cycle 6: HTML escaping --------------------


def test_html_escape_worker_name_with_lt(db_path: str) -> None:
    _seed_session(db_path, _SESSION_A, profile={"first_name": "<Alice>"})
    result = compose_digest(
        _SESSION_A, _FOR_DATE, db_path=db_path, now=_NOW_FROZEN,
    )
    assert "&lt;Alice&gt;" in result.html
    # plaintext keeps raw value
    assert "<Alice>" in result.text


def test_html_escape_appointment_title(db_path: str) -> None:
    _attended_yesterday(db_path=db_path, title="<script>alert('x')</script>")
    result = compose_digest(
        _SESSION_A, _FOR_DATE, db_path=db_path, now=_NOW_FROZEN,
    )
    assert "<script>" not in result.html
    assert "&lt;script&gt;" in result.html


# -------------------- Cycle 7: section counts + snapshots --------------------


def test_section_counts_accurate(db_path: str) -> None:
    """2 yesterday wins + 1 today upcoming + 0 week + 0 stall (fresh signals)."""
    _attended_yesterday(db_path=db_path, title="DMV visit A")
    _create_appointment(
        db_path=db_path,
        starts_at=_at(_FOR_DATE - timedelta(days=1), 16),
        title="DMV visit B",
    )
    # mark the second yesterday appt attended too
    second_attended = scheduler.list_by_session(_SESSION_A, db_path=db_path)[-1]
    scheduler.mark_attended(second_attended.id, db_path=db_path)
    # one future appt today
    _create_appointment(
        db_path=db_path,
        starts_at=_at(_FOR_DATE, 15),
        title="Career center today",
        appt_type=AppointmentType.CAREER_CENTER,
        location_name="Center",
    )
    # Note: stall is 0 here because attended-yesterday itself is a
    # recent progress signal — the stall detector sees the session as
    # healthy. A separate test covers the HARD case in isolation.
    result = compose_digest(
        _SESSION_A, _FOR_DATE, db_path=db_path, now=_NOW_FROZEN,
    )
    assert result.section_counts == {
        "yesterday": 2, "today": 1, "week": 0, "stall": 0,
    }


def test_snapshot_all_empty(db_path: str) -> None:
    result = compose_digest(
        _SESSION_A, _FOR_DATE, db_path=db_path, now=_NOW_FROZEN,
    )
    # Key structural substrings (avoids brittleness on small changes)
    expected_substrings = [
        "Hi friend",
        "Nothing new today",
    ]
    for s in expected_substrings:
        assert s in result.html, f"missing in html: {s!r}"
        assert s in result.text, f"missing in text: {s!r}"
    # No section headings when fully empty
    assert "<h2>" not in result.html


def test_snapshot_fully_populated(db_path: str) -> None:
    """Snapshot of all sections with yesterday/today/week populated.

    Stall section is omitted here because recent yesterday wins mean the
    stall detector (correctly) sees the session as healthy. A separate
    test (`test_stall_alert_hard_renders_advisor_cta`) covers the stall
    path in isolation.
    """
    _seed_session(db_path, _SESSION_A, profile={"first_name": "Alice"})
    _attended_yesterday(db_path=db_path, title="DMV appt")
    _filed_application(db_path=db_path, company="Acme", role="Driver")
    _seed_barrier_cleared(db_path=db_path, barrier="dmv")
    _create_appointment(
        db_path=db_path,
        starts_at=_at(_FOR_DATE, 15),
        title="Career center today",
        appt_type=AppointmentType.CAREER_CENTER,
        location_name="Center",
    )
    _create_appointment(
        db_path=db_path,
        starts_at=_at(_FOR_DATE + timedelta(days=3), 10),
        title="Court hearing",
        appt_type=AppointmentType.COURT_HEARING,
        location_name="Court",
    )
    result = compose_digest(
        _SESSION_A, _FOR_DATE, db_path=db_path, now=_NOW_FROZEN,
    )
    expected = [
        "Hi Alice",
        "Yesterday",
        "DMV appt",
        "Acme",
        "Driver",
        "dmv",
        "Today",
        "Career center today",
        "This week",
        "Court hearing",
    ]
    for s in expected:
        assert s in result.html, f"missing in html: {s!r}"
        assert s in result.text, f"missing in text: {s!r}"
