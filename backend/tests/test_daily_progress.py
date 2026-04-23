"""Tests for plan.daily_progress — nightly retro (T12.22).

Covers the pure classification core (`_derive_done_flags`), the single-day
evidence wrapper (`collect_for_date`), the end-to-end `run_nightly_retro`
orchestrator, and the persistence round-trip (`persist` / `load`).

Expected-actions source (Option B): the `ActionPlan` produced by T-series
plan builders is phase-based with no per-day binding, so the retro's
contract defines "expected actions for a date" as the scheduled
appointments on that date. This keeps the retro deterministic and
data-driven off tables that already exist.
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
from app.modules.jobs import applications
from app.modules.plan import daily_progress as dp
from app.modules.plan.daily_progress import (
    ActionClassification,
    RetroAction,
    RetroResult,
    _derive_done_flags,
    collect_for_date,
    load,
    persist,
    run_nightly_retro,
)
from app.modules.plan.evidence_collector import EvidenceBundle

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
    path = str(tmp_path / "retro.db")
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
    return datetime.combine(d, time(12, 0, tzinfo=timezone.utc))


def _make_appointment(
    *,
    session_id: str,
    starts_at: datetime,
    status: AppointmentStatus,
    db_path: str,
    title: str = "DMV appointment",
    appt_type: AppointmentType = AppointmentType.DMV,
) -> Appointment:
    appt = Appointment(
        session_id=session_id,
        type=appt_type,
        title=title,
        starts_at=starts_at,
        ends_at=starts_at + timedelta(hours=1),
        location_name="Somewhere",
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


def _empty_bundle(sid: str, d: date) -> EvidenceBundle:
    return EvidenceBundle(
        session_id=sid,
        date_range_start=d,
        date_range_end=d,
    )


# -------------------- Pure classification tests --------------------


def test_empty_plan_returns_empty_actions() -> None:
    result = _derive_done_flags([], _empty_bundle(_SESSION_A, date(2026, 4, 22)))
    assert result == []


def test_no_evidence_all_undone() -> None:
    expected = [
        {"action_id": "submit_3_applications", "title": "Submit 3 applications"},
        {"action_id": "dmv_appointment", "title": "DMV appointment"},
    ]
    result = _derive_done_flags(expected, _empty_bundle(_SESSION_A, date(2026, 4, 22)))
    assert len(result) == 2
    assert all(a.classification is ActionClassification.UNDONE for a in result)


def test_attended_appointment_classified_done(db_path: str) -> None:
    day = date(2026, 4, 22)
    _make_appointment(
        session_id=_SESSION_A,
        starts_at=_midday(day),
        status=AppointmentStatus.ATTENDED,
        db_path=db_path,
        title="DMV appointment",
    )
    bundle = collect_for_date(_SESSION_A, day, db_path=db_path)
    expected = [{"action_id": "dmv_appointment", "title": "DMV appointment"}]
    result = _derive_done_flags(expected, bundle)
    assert len(result) == 1
    assert result[0].classification is ActionClassification.DONE


def test_missed_appointment_classified_undone(db_path: str) -> None:
    day = date(2026, 4, 22)
    _make_appointment(
        session_id=_SESSION_A,
        starts_at=_midday(day),
        status=AppointmentStatus.MISSED,
        db_path=db_path,
        title="DMV appointment",
    )
    bundle = collect_for_date(_SESSION_A, day, db_path=db_path)
    expected = [{"action_id": "dmv_appointment", "title": "DMV appointment"}]
    result = _derive_done_flags(expected, bundle)
    assert len(result) == 1
    assert result[0].classification is ActionClassification.UNDONE
    assert result[0].evidence_note is not None
    assert "missed" in result[0].evidence_note.lower()


def test_applications_count_partial() -> None:
    # Expected: submit 3 applications. Bundle shows 1 filed => PARTIAL.
    bundle = EvidenceBundle(
        session_id=_SESSION_A,
        date_range_start=date(2026, 4, 22),
        date_range_end=date(2026, 4, 22),
    )
    # Simulate 1 application filed — avoid DB hit by poking the list directly.
    # Use a dict-like placeholder that satisfies .model_dump_json in persist,
    # but _derive_done_flags only inspects the length here.
    from app.modules.jobs.types import JobApplication

    bundle.applications_filed = [
        JobApplication(
            session_id=_SESSION_A,
            match_source="indeed",
            match_url="https://x.test/1",
            company="A",
            role="R",
            status=JobApplicationStatus.APPLIED,
        )
    ]
    expected = [{"action_id": "submit_3_apps", "title": "Submit 3 applications"}]
    result = _derive_done_flags(expected, bundle)
    assert result[0].classification is ActionClassification.PARTIAL


def test_applications_count_done_when_threshold_met() -> None:
    from app.modules.jobs.types import JobApplication

    bundle = EvidenceBundle(
        session_id=_SESSION_A,
        date_range_start=date(2026, 4, 22),
        date_range_end=date(2026, 4, 22),
    )
    bundle.applications_filed = [
        JobApplication(
            session_id=_SESSION_A,
            match_source="indeed",
            match_url=f"https://x.test/{i}",
            company="A",
            role="R",
            status=JobApplicationStatus.APPLIED,
        )
        for i in range(3)
    ]
    expected = [{"action_id": "submit_3_apps", "title": "Submit 3 applications"}]
    result = _derive_done_flags(expected, bundle)
    assert result[0].classification is ActionClassification.DONE


def test_completion_ratio_formula(db_path: str) -> None:
    # Build a 5-action expected set where 3 are matched by evidence (DONE),
    # 2 are unmatched (UNDONE). Ratio must be 0.6.
    day = date(2026, 4, 22)
    for i in range(3):
        _make_appointment(
            session_id=_SESSION_A,
            starts_at=_midday(day) + timedelta(hours=i),
            status=AppointmentStatus.ATTENDED,
            db_path=db_path,
            title=f"Appt {i}",
        )
    result = run_nightly_retro(_SESSION_A, day, db_path=db_path)
    # run_nightly_retro builds expected from scheduled+attended+missed on the
    # day. With 3 attended, that's 3 expected, 3 done, ratio 1.0.
    assert result.completion_ratio == 1.0
    # Now create a session with 5 expected: 3 attended + 2 missed.
    for i in range(2):
        _make_appointment(
            session_id=_SESSION_B,
            starts_at=_midday(day) + timedelta(hours=i),
            status=AppointmentStatus.ATTENDED,
            db_path=db_path,
            title=f"Hit {i}",
        )
    for i in range(3):
        _make_appointment(
            session_id=_SESSION_B,
            starts_at=_midday(day) + timedelta(hours=4 + i),
            status=AppointmentStatus.MISSED,
            db_path=db_path,
            title=f"Miss {i}",
        )
    result_b = run_nightly_retro(_SESSION_B, day, db_path=db_path)
    # 5 expected, 2 attended => 2/5 = 0.4
    assert result_b.completion_ratio == pytest.approx(0.4)


# -------------------- Wrapper tests --------------------


def test_collect_for_date_uses_single_day_range(monkeypatch) -> None:
    """collect_for_date must invoke collect_evidence with start==end==for_date."""
    seen: dict = {}

    def _spy(session_id, *, start, end, db_path):
        seen["session_id"] = session_id
        seen["start"] = start
        seen["end"] = end
        return EvidenceBundle(
            session_id=session_id,
            date_range_start=start,
            date_range_end=end,
        )

    monkeypatch.setattr(dp, "collect_evidence", _spy)
    target = date(2026, 4, 22)
    result = collect_for_date(_SESSION_A, target, db_path="ignored")
    assert seen == {"session_id": _SESSION_A, "start": target, "end": target}
    assert result.date_range_start == target
    assert result.date_range_end == target


# -------------------- End-to-end retro tests --------------------


def test_empty_retro_no_expected_actions(db_path: str) -> None:
    # No appointments, no evidence — empty retro.
    day = date(2026, 4, 22)
    result = run_nightly_retro(_SESSION_A, day, db_path=db_path)
    assert result.session_id == _SESSION_A
    assert result.for_date == day
    assert result.actions == []
    assert result.completion_ratio == 0
    assert isinstance(result.summary, str) and result.summary


def test_full_evidence_all_done(db_path: str) -> None:
    day = date(2026, 4, 22)
    _make_appointment(
        session_id=_SESSION_A,
        starts_at=_midday(day),
        status=AppointmentStatus.ATTENDED,
        db_path=db_path,
        title="DMV appointment",
    )
    result = run_nightly_retro(_SESSION_A, day, db_path=db_path)
    assert len(result.actions) == 1
    assert result.actions[0].classification is ActionClassification.DONE
    assert result.completion_ratio == 1.0


def test_mixed_done_partial_undone(db_path: str) -> None:
    day = date(2026, 4, 22)
    _make_appointment(
        session_id=_SESSION_A,
        starts_at=_midday(day),
        status=AppointmentStatus.ATTENDED,
        db_path=db_path,
        title="Attended appt",
    )
    _make_appointment(
        session_id=_SESSION_A,
        starts_at=_midday(day) + timedelta(hours=2),
        status=AppointmentStatus.MISSED,
        db_path=db_path,
        title="Missed appt",
    )
    result = run_nightly_retro(_SESSION_A, day, db_path=db_path)
    classes = {a.classification for a in result.actions}
    assert ActionClassification.DONE in classes
    assert ActionClassification.UNDONE in classes


# -------------------- Persistence tests --------------------


def test_persist_and_load_round_trip(db_path: str) -> None:
    day = date(2026, 4, 22)
    original = RetroResult(
        session_id=_SESSION_A,
        for_date=day,
        actions=[
            RetroAction(
                action_id="a1",
                title="Do thing",
                classification=ActionClassification.DONE,
                evidence_note="attended",
            ),
            RetroAction(
                action_id="a2",
                title="Skip thing",
                classification=ActionClassification.UNDONE,
            ),
        ],
        completion_ratio=0.5,
        summary="1/2 actions complete",
    )
    persist(original, db_path=db_path)
    loaded = load(_SESSION_A, day, db_path=db_path)
    assert loaded is not None
    assert loaded.session_id == _SESSION_A
    assert loaded.for_date == day
    assert loaded.completion_ratio == 0.5
    assert len(loaded.actions) == 2
    assert loaded.actions[0].action_id == "a1"
    assert loaded.actions[0].classification is ActionClassification.DONE
    assert loaded.actions[1].classification is ActionClassification.UNDONE


def test_load_missing_returns_none(db_path: str) -> None:
    assert load(_SESSION_A, date(2026, 4, 22), db_path=db_path) is None


def test_idempotent_rerun_upserts(db_path: str) -> None:
    day = date(2026, 4, 22)
    _make_appointment(
        session_id=_SESSION_A,
        starts_at=_midday(day),
        status=AppointmentStatus.ATTENDED,
        db_path=db_path,
        title="X",
    )
    first = run_nightly_retro(_SESSION_A, day, db_path=db_path)
    second = run_nightly_retro(_SESSION_A, day, db_path=db_path)
    # Exactly one row in the snapshots table for this (session, date).
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM daily_progress_snapshots "
            "WHERE session_id = ? AND date = ?",
            (_SESSION_A, day.isoformat()),
        ).fetchone()
    finally:
        conn.close()
    assert row[0] == 1
    assert first.completion_ratio == second.completion_ratio


def test_classifications_json_persists_as_list_of_dicts(db_path: str) -> None:
    day = date(2026, 4, 22)
    _make_appointment(
        session_id=_SESSION_A,
        starts_at=_midday(day),
        status=AppointmentStatus.ATTENDED,
        db_path=db_path,
        title="Foo",
    )
    run_nightly_retro(_SESSION_A, day, db_path=db_path)
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT classifications_json FROM daily_progress_snapshots "
            "WHERE session_id = ? AND date = ?",
            (_SESSION_A, day.isoformat()),
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    parsed = json.loads(row[0])
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["classification"] in {
        "done", "undone", "partial",
    }
    assert "action_id" in parsed[0]
    assert "title" in parsed[0]
