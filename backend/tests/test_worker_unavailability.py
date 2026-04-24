"""Tests for worker unavailability blocks persistence (T12.8a).

Covers:
- add_unavailability_block persists rows with correct fields
- Validation: start >= end, invalid time formats, invalid day_of_week
- get_unavailable_blocks returns the dict shape T12.8 availability consumes
- Isolation by session_id
- Integration with compute_available_slots (slots are subtracted)
- list_schedule_events returns full records
- remove_unavailability_block deletes a row
- FK CASCADE on session delete
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from app.core.migrations import runner
from app.modules.appointments.availability import compute_available_slots
from app.modules.appointments.service_config import ServiceConfig
from app.modules.appointments.unavailability import (
    UnavailabilityBlock,
    UnavailabilityError,
    add_unavailability_block,
    get_unavailable_blocks,
    list_schedule_events,
    remove_unavailability_block,
)

_SESSION_A = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
_SESSION_B = "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"


# -------------------- Fixtures --------------------


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "unavail.db")
    runner.apply_pending(path)
    _seed_sessions(path, [_SESSION_A, _SESSION_B])
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


def _select_raw(path: str, session_id: str) -> list[tuple]:
    conn = sqlite3.connect(path)
    try:
        return conn.execute(
            "SELECT id, session_id, day_of_week, start_time, end_time, reason "
            "FROM worker_unavailability WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
    finally:
        conn.close()


# -------------------- Cycle 1: persistence --------------------


def test_add_unavailability_block_inserts_row(db_path: str) -> None:
    """add_unavailability_block writes a row with the provided fields."""
    block = add_unavailability_block(
        _SESSION_A,
        day_of_week=1,  # Tuesday
        start_time="13:00",
        end_time="15:00",
        reason="childcare pickup",
        db_path=db_path,
    )
    assert isinstance(block, UnavailabilityBlock)
    assert block.id is not None
    assert block.session_id == _SESSION_A
    assert block.day_of_week == 1
    assert block.start_time == "13:00"
    assert block.end_time == "15:00"
    assert block.reason == "childcare pickup"

    rows = _select_raw(db_path, _SESSION_A)
    assert len(rows) == 1
    _, sid, dow, start, end, reason = rows[0]
    assert sid == _SESSION_A
    assert dow == 1
    assert start == "13:00"
    assert end == "15:00"
    assert reason == "childcare pickup"


def test_add_reason_optional(db_path: str) -> None:
    """reason may be omitted (None)."""
    block = add_unavailability_block(
        _SESSION_A,
        day_of_week=3,
        start_time="09:00",
        end_time="10:00",
        db_path=db_path,
    )
    assert block.reason is None


# -------------------- Cycle 2: validation --------------------


def test_add_rejects_start_equals_end(db_path: str) -> None:
    """Zero-length block raises UnavailabilityError."""
    with pytest.raises(UnavailabilityError):
        add_unavailability_block(
            _SESSION_A,
            day_of_week=1,
            start_time="13:00",
            end_time="13:00",
            db_path=db_path,
        )


def test_add_rejects_start_after_end(db_path: str) -> None:
    """Overnight / inverted blocks raise."""
    with pytest.raises(UnavailabilityError):
        add_unavailability_block(
            _SESSION_A,
            day_of_week=1,
            start_time="15:00",
            end_time="13:00",
            db_path=db_path,
        )


def test_add_rejects_invalid_time_format(db_path: str) -> None:
    """Hour out of range raises."""
    with pytest.raises(UnavailabilityError):
        add_unavailability_block(
            _SESSION_A,
            day_of_week=1,
            start_time="25:00",
            end_time="26:00",
            db_path=db_path,
        )


def test_add_rejects_malformed_time(db_path: str) -> None:
    """Non-HH:MM strings raise."""
    with pytest.raises(UnavailabilityError):
        add_unavailability_block(
            _SESSION_A,
            day_of_week=1,
            start_time="9:00",  # missing leading zero
            end_time="10:00",
            db_path=db_path,
        )


def test_add_rejects_minute_out_of_range(db_path: str) -> None:
    """Minute > 59 raises."""
    with pytest.raises(UnavailabilityError):
        add_unavailability_block(
            _SESSION_A,
            day_of_week=1,
            start_time="09:60",
            end_time="10:00",
            db_path=db_path,
        )


def test_add_rejects_invalid_day_of_week(db_path: str) -> None:
    """day_of_week must be 0..6."""
    with pytest.raises(UnavailabilityError):
        add_unavailability_block(
            _SESSION_A,
            day_of_week=7,
            start_time="09:00",
            end_time="10:00",
            db_path=db_path,
        )
    with pytest.raises(UnavailabilityError):
        add_unavailability_block(
            _SESSION_A,
            day_of_week=-1,
            start_time="09:00",
            end_time="10:00",
            db_path=db_path,
        )


# -------------------- Cycle 3: read / shape --------------------


def test_get_unavailable_blocks_returns_shape_availability_expects(
    db_path: str,
) -> None:
    """get_unavailable_blocks returns list of dicts with the exact keys
    compute_available_slots consumes for recurring blocks."""
    add_unavailability_block(
        _SESSION_A,
        day_of_week=1,
        start_time="13:00",
        end_time="15:00",
        db_path=db_path,
    )
    blocks = get_unavailable_blocks(_SESSION_A, db_path=db_path)
    assert len(blocks) == 1
    b = blocks[0]
    assert set(b.keys()) == {"day_of_week", "start_time", "end_time"}
    assert b["day_of_week"] == 1
    assert b["start_time"] == "13:00"
    assert b["end_time"] == "15:00"


def test_get_unavailable_blocks_empty_for_no_blocks(db_path: str) -> None:
    """Returns empty list when the session has no blocks."""
    assert get_unavailable_blocks(_SESSION_A, db_path=db_path) == []


def test_get_blocks_for_other_session_isolated(db_path: str) -> None:
    """A session's query never returns another session's blocks."""
    add_unavailability_block(
        _SESSION_A, day_of_week=1, start_time="13:00", end_time="15:00",
        db_path=db_path,
    )
    add_unavailability_block(
        _SESSION_B, day_of_week=2, start_time="09:00", end_time="11:00",
        db_path=db_path,
    )
    a_blocks = get_unavailable_blocks(_SESSION_A, db_path=db_path)
    b_blocks = get_unavailable_blocks(_SESSION_B, db_path=db_path)
    assert len(a_blocks) == 1 and a_blocks[0]["day_of_week"] == 1
    assert len(b_blocks) == 1 and b_blocks[0]["day_of_week"] == 2


# -------------------- Cycle 4: availability engine integration --------------------


def test_availability_engine_integration(db_path: str) -> None:
    """compute_available_slots subtracts blocks returned by get_unavailable_blocks."""
    # Tuesday 13:00-15:00 block
    add_unavailability_block(
        _SESSION_A,
        day_of_week=1,
        start_time="13:00",
        end_time="15:00",
        db_path=db_path,
    )
    service = ServiceConfig(
        service_type="dmv",
        duration_minutes=30,
        hours_local=[("09:00", "17:00")],
        closed_days_of_week=set(),
        holidays=[],
    )
    # 2026-06-02 is a Tuesday (weekday=1).
    day = date(2026, 6, 2)
    blocks = get_unavailable_blocks(_SESSION_A, db_path=db_path)
    slots = compute_available_slots(
        service, [], city="montgomery", day=day, unavailability_blocks=blocks,
    )
    local_hours = {(s.hour, s.minute) for s in slots}
    # Slots that overlap 13:00-15:00 window must be absent: 13:00, 13:30,
    # 14:00, 14:30. (A 12:30 slot ends at 13:00 -> adjacent, not overlapping.)
    for blocked in [(13, 0), (13, 30), (14, 0), (14, 30)]:
        assert blocked not in local_hours, f"slot {blocked} should be blocked"
    # Slots outside the window remain available.
    assert (9, 0) in local_hours
    assert (12, 30) in local_hours  # ends at 13:00, adjacent not overlapping
    assert (15, 0) in local_hours


def test_availability_engine_ignores_other_weekdays(db_path: str) -> None:
    """A Tuesday block does not affect a Wednesday's availability."""
    add_unavailability_block(
        _SESSION_A, day_of_week=1, start_time="13:00", end_time="15:00",
        db_path=db_path,
    )
    service = ServiceConfig(
        service_type="dmv",
        duration_minutes=30,
        hours_local=[("09:00", "17:00")],
        closed_days_of_week=set(),
        holidays=[],
    )
    # 2026-06-03 is a Wednesday (weekday=2).
    blocks = get_unavailable_blocks(_SESSION_A, db_path=db_path)
    slots = compute_available_slots(
        service, [], city="montgomery", day=date(2026, 6, 3),
        unavailability_blocks=blocks,
    )
    local_hours = {(s.hour, s.minute) for s in slots}
    for t in [(13, 0), (13, 30), (14, 0), (14, 30)]:
        assert t in local_hours


# -------------------- Cycle 5: list / remove / cascade --------------------


def test_list_schedule_events_returns_full_records(db_path: str) -> None:
    """list_schedule_events returns UnavailabilityBlock records for UI display."""
    add_unavailability_block(
        _SESSION_A, day_of_week=1, start_time="13:00", end_time="15:00",
        reason="school pickup", db_path=db_path,
    )
    add_unavailability_block(
        _SESSION_A, day_of_week=3, start_time="09:00", end_time="10:00",
        db_path=db_path,
    )
    events = list_schedule_events(
        _SESSION_A,
        date_range=(date(2026, 6, 1), date(2026, 6, 7)),
        db_path=db_path,
    )
    assert len(events) == 2
    assert all(isinstance(e, UnavailabilityBlock) for e in events)
    assert all(e.id is not None and e.session_id == _SESSION_A for e in events)
    reasons = {e.reason for e in events}
    assert "school pickup" in reasons
    assert None in reasons


def test_remove_unavailability_block_deletes(db_path: str) -> None:
    """remove_unavailability_block removes the row by id."""
    block = add_unavailability_block(
        _SESSION_A, day_of_week=1, start_time="13:00", end_time="15:00",
        db_path=db_path,
    )
    assert block.id is not None
    remove_unavailability_block(block.id, db_path=db_path)
    assert _select_raw(db_path, _SESSION_A) == []


def test_cascade_on_session_delete(db_path: str) -> None:
    """Blocks are deleted when the owning session row is deleted (FK CASCADE)."""
    add_unavailability_block(
        _SESSION_A, day_of_week=1, start_time="13:00", end_time="15:00",
        db_path=db_path,
    )
    add_unavailability_block(
        _SESSION_A, day_of_week=2, start_time="09:00", end_time="10:00",
        db_path=db_path,
    )
    assert len(_select_raw(db_path, _SESSION_A)) == 2

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DELETE FROM sessions WHERE id = ?", (_SESSION_A,))
        conn.commit()
    finally:
        conn.close()

    assert _select_raw(db_path, _SESSION_A) == []
