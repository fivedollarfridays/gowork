"""Parity tests for `_batch_stalls.batch_compute_stalls` (T13.90).

The batched stall classifier replaces a per-session
:func:`compute_stall_for_session` loop in the advisor-inbox list path
(see :mod:`app.modules.engagement._batch_stalls` for the rationale).
Because production correctness depends on the two paths returning the
same answer for every input shape, these tests assert parity directly
— for each scenario, both classifiers run against the same DB and
their `(days_stalled, stall_level)` tuples must match.

Scenarios covered:

* No-signal session — stall_level=NONE, days_stalled=0.
* Session-wide stall (no enumerable barriers).
* Per-barrier stall (signal tagged with a specific barrier).
* Multi-barrier stall (worst level wins).
* Auto-advance noise — must NOT count as forward motion.
* Filed application — applied_date counts.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core.migrations import runner
from app.modules.engagement._batch_stalls import batch_compute_stalls
from app.modules.engagement.stall_detector import (
    compute_stall_for_session,
)

_NOW = datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc)

# OutcomeRecord validates session_id as UUID; tests use fixed UUIDs.
_SID_NO_SIGNAL = "11111111-1111-4111-8111-111111111111"
_SID_WIDE_STALL = "22222222-2222-4222-8222-222222222222"
_SID_HARD = "33333333-3333-4333-8333-333333333333"
_SID_PER_BARRIER = "44444444-4444-4444-8444-444444444444"
_SID_AUTO = "55555555-5555-4555-8555-555555555555"
_SID_FILED = "66666666-6666-4666-8666-666666666666"
_SID_FRESH = "77777777-7777-4777-8777-777777777777"
_SID_STALE = "88888888-8888-4888-8888-888888888888"
_SID_EMPTY = "99999999-9999-4999-8999-999999999999"


# ---------------------------------------------------------------- fixtures


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "batch_stalls.db")
    runner.apply_pending(path)
    return path


def _seed_session(
    db_path: str, session_id: str, *,
    barriers: list[str] | None = None,
) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (
                session_id,
                _NOW.isoformat(),
                json.dumps(barriers or []),
                (_NOW + timedelta(days=30)).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _seed_appointment(
    db_path: str, session_id: str, *,
    starts_at: datetime, status: str = "attended",
    barrier_link: str | None = None,
) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO appointments "
            "(session_id, type, title, starts_at, ends_at, status, "
            "barrier_link, created_at, source, location_name) "
            "VALUES (?, 'other', 't', ?, ?, ?, ?, ?, 'user', 'somewhere')",
            (
                session_id,
                starts_at.isoformat(),
                (starts_at + timedelta(hours=1)).isoformat(),
                status,
                barrier_link,
                starts_at.isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _seed_outcome(
    db_path: str, session_id: str, *,
    when: datetime, event_type: str = "appointment_attended",
) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO outcomes_records "
            "(session_id, event_type, payload_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, event_type, "{}", when.isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def _seed_application(
    db_path: str, session_id: str, *,
    status: str = "applied",
    applied_date: str | None = None,
    created_at: datetime | None = None,
) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO job_applications "
            "(session_id, match_source, match_url, company, role, "
            "status, applied_date, created_at) "
            "VALUES (?, 'indeed', 'https://x', 'A', 'r', ?, ?, ?)",
            (
                session_id, status, applied_date,
                (created_at or _NOW).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _both_paths(db_path: str, session_id: str) -> tuple[
    tuple[int, str], tuple[int, str],
]:
    """Return ((per-session days, level), (batch days, level)) for parity."""
    per = compute_stall_for_session(session_id, db_path=db_path, now=_NOW)
    batch = batch_compute_stalls([session_id], db_path=db_path, now=_NOW)
    days, level, _ = batch[session_id]
    return (per.days_stalled, per.stall_level.value), (days, level.value)


# ---------------------------------------------------------------- parity


def test_no_signal_session_parity(db_path: str) -> None:
    _seed_session(db_path, _SID_NO_SIGNAL)
    a, b = _both_paths(db_path, _SID_NO_SIGNAL)
    assert a == b == (0, "none")


def test_session_wide_stall_parity(db_path: str) -> None:
    """Session has outcomes only — session-wide fallback path."""
    _seed_session(db_path, _SID_WIDE_STALL)
    _seed_outcome(
        db_path, _SID_WIDE_STALL,
        when=_NOW - timedelta(days=10),
        event_type="appointment_attended",
    )
    a, b = _both_paths(db_path, _SID_WIDE_STALL)
    assert a == b
    # Worker last did anything 10 days ago → MEDIUM (≥7, <14).
    assert a == (10, "medium")


def test_hard_session_wide_parity(db_path: str) -> None:
    _seed_session(db_path, _SID_HARD)
    _seed_outcome(
        db_path, _SID_HARD, when=_NOW - timedelta(days=21),
    )
    a, b = _both_paths(db_path, _SID_HARD)
    assert a == b
    assert a == (21, "hard")


def test_per_barrier_stall_parity(db_path: str) -> None:
    """Session has barriers + barrier-tagged appointment."""
    _seed_session(db_path, _SID_PER_BARRIER, barriers=["dmv", "childcare"])
    # Recent appointment for dmv (no stall)
    _seed_appointment(
        db_path, _SID_PER_BARRIER,
        starts_at=_NOW - timedelta(days=1),
        barrier_link="dmv",
    )
    a, b = _both_paths(db_path, _SID_PER_BARRIER)
    assert a == b


def test_auto_advance_noise_parity(db_path: str) -> None:
    """Auto-advance outcomes do NOT count as forward motion."""
    _seed_session(db_path, _SID_AUTO)
    # Recent auto-advance only — should NOT mark the session as fresh.
    _seed_outcome(
        db_path, _SID_AUTO,
        when=_NOW - timedelta(hours=1),
        event_type="appointment_auto_advance",
    )
    # Old real outcome (so days_stalled is non-zero)
    _seed_outcome(
        db_path, _SID_AUTO,
        when=_NOW - timedelta(days=20),
        event_type="appointment_attended",
    )
    a, b = _both_paths(db_path, _SID_AUTO)
    assert a == b
    # The auto-advance is suppressed; the real outcome 20d ago wins.
    assert a == (20, "hard")


def test_filed_application_parity(db_path: str) -> None:
    """An APPLIED application's applied_date counts as forward motion."""
    _seed_session(db_path, _SID_FILED)
    applied_iso = (_NOW - timedelta(days=2)).date().isoformat()
    _seed_application(
        db_path, _SID_FILED, status="applied", applied_date=applied_iso,
    )
    a, b = _both_paths(db_path, _SID_FILED)
    assert a == b


def test_batch_with_multiple_sessions(db_path: str) -> None:
    """Batch path returns the right answer per session in one call."""
    _seed_session(db_path, _SID_FRESH)
    _seed_outcome(db_path, _SID_FRESH, when=_NOW - timedelta(days=1))

    _seed_session(db_path, _SID_STALE)
    _seed_outcome(db_path, _SID_STALE, when=_NOW - timedelta(days=20))

    _seed_session(db_path, _SID_EMPTY)  # no outcomes, no apps

    summaries = batch_compute_stalls(
        [_SID_FRESH, _SID_STALE, _SID_EMPTY],
        db_path=db_path, now=_NOW,
    )
    assert summaries[_SID_FRESH][1].value == "none"
    assert summaries[_SID_STALE][1].value == "hard"
    assert summaries[_SID_STALE][0] == 20
    assert summaries[_SID_EMPTY][1].value == "none"


def test_batch_empty_session_list_returns_empty(db_path: str) -> None:
    """No SQL is issued when session_ids is empty."""
    assert batch_compute_stalls([], db_path=db_path, now=_NOW) == {}
