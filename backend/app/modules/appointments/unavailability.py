"""Worker unavailability block persistence (T12.8a).

Ported from ``ops:lib/schedule.py`` and adapted to MontGoWork's
``worker_unavailability`` table (session-scoped, day-of-week + HH:MM).

Public API:
    * ``UnavailabilityBlock`` — frozen dataclass record.
    * ``UnavailabilityError`` — ValueError subtype for bad input.
    * ``add_unavailability_block`` — persist a recurring weekly block.
    * ``get_unavailable_blocks`` — dict shape consumed by
      ``availability.compute_available_slots`` (``{"day_of_week",
      "start_time", "end_time"}``).
    * ``list_schedule_events`` — full records for UI display.
    * ``remove_unavailability_block`` — delete by id.

Validation mirrors T12.8:
    * ``HH:MM`` strict (hour 0-23, minute 0-59).
    * ``start >= end`` -> error (no overnight blocks).
    * ``day_of_week`` must be 0-6 (Monday-Sunday).
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path

__all__ = [
    "UnavailabilityBlock",
    "UnavailabilityError",
    "add_unavailability_block",
    "get_unavailable_blocks",
    "list_schedule_events",
    "remove_unavailability_block",
]

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

_SELECT_COLS = "id, session_id, day_of_week, start_time, end_time, reason"

_INSERT_SQL = (
    "INSERT INTO worker_unavailability "
    "(session_id, day_of_week, start_time, end_time, reason) "
    "VALUES (?, ?, ?, ?, ?)"
)
_SELECT_DICT_SQL = (
    "SELECT day_of_week, start_time, end_time FROM worker_unavailability "
    "WHERE session_id = ? ORDER BY day_of_week, start_time, id"
)
_SELECT_FULL_SQL = (
    f"SELECT {_SELECT_COLS} FROM worker_unavailability "
    "WHERE session_id = ? ORDER BY day_of_week, start_time, id"
)
_DELETE_SQL = "DELETE FROM worker_unavailability WHERE id = ?"


class UnavailabilityError(ValueError):
    """Raised when an unavailability block fails validation."""


@dataclass(frozen=True)
class UnavailabilityBlock:
    """A worker's weekly recurring unavailability window.

    ``id`` is ``None`` until persisted. ``day_of_week`` uses Python's
    ``weekday()`` convention (0=Monday, 6=Sunday). Times are ``HH:MM``
     strings in the worker's local tz (resolved by the availability engine).
    """

    id: int | None
    session_id: str
    day_of_week: int
    start_time: str
    end_time: str
    reason: str | None = None


def _connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _validate(day_of_week: int, start_time: str, end_time: str) -> None:
    """Reject invalid day-of-week, malformed times, and non-positive ranges."""
    if not 0 <= day_of_week <= 6:
        raise UnavailabilityError(
            f"day_of_week must be 0..6 (got {day_of_week!r})"
        )
    if not _TIME_RE.match(start_time):
        raise UnavailabilityError(
            f"start_time must be HH:MM (got {start_time!r})"
        )
    if not _TIME_RE.match(end_time):
        raise UnavailabilityError(
            f"end_time must be HH:MM (got {end_time!r})"
        )
    if start_time >= end_time:
        raise UnavailabilityError(
            f"start_time {start_time!r} must be earlier than "
            f"end_time {end_time!r}"
        )


def add_unavailability_block(
    session_id: str,
    day_of_week: int,
    start_time: str,
    end_time: str,
    *,
    reason: str | None = None,
    db_path: str | Path,
) -> UnavailabilityBlock:
    """Persist a recurring weekly unavailability block.

    Raises ``UnavailabilityError`` if times are malformed, ``start >= end``,
    or day_of_week is outside 0..6.
    """
    _validate(day_of_week, start_time, end_time)
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            _INSERT_SQL,
            (session_id, day_of_week, start_time, end_time, reason),
        )
        conn.commit()
        new_id = int(cur.lastrowid)
    finally:
        conn.close()
    return UnavailabilityBlock(
        id=new_id,
        session_id=session_id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        reason=reason,
    )


def get_unavailable_blocks(
    session_id: str,
    *,
    db_path: str | Path,
) -> list[dict]:
    """Return blocks in the exact shape T12.8 ``availability.py`` consumes.

    Each dict has keys ``day_of_week`` (int), ``start_time`` (str),
    ``end_time`` (str). Empty list when the session has no blocks.
    """
    conn = _connect(db_path)
    try:
        rows = conn.execute(_SELECT_DICT_SQL, (session_id,)).fetchall()
    finally:
        conn.close()
    return [
        {
            "day_of_week": int(dow),
            "start_time": start,
            "end_time": end,
        }
        for dow, start, end in rows
    ]


def list_schedule_events(
    session_id: str,
    date_range: tuple[date, date],
    *,
    db_path: str | Path,
) -> list[UnavailabilityBlock]:
    """Return all blocks as full UnavailabilityBlock records for UI display.

    ``date_range`` is accepted for API symmetry with a future one-off events
    table; because every block stored here is weekly-recurring, every block
    for the session is returned and the UI is expected to expand them across
    the visible window.
    """
    _ = date_range  # reserved for future filtering of one-off events
    conn = _connect(db_path)
    try:
        rows = conn.execute(_SELECT_FULL_SQL, (session_id,)).fetchall()
    finally:
        conn.close()
    return [
        UnavailabilityBlock(
            id=int(rid),
            session_id=sid,
            day_of_week=int(dow),
            start_time=start,
            end_time=end,
            reason=reason,
        )
        for rid, sid, dow, start, end, reason in rows
    ]


def remove_unavailability_block(
    block_id: int,
    *,
    db_path: str | Path,
) -> None:
    """Delete a block by id. Silent if the id does not exist."""
    conn = _connect(db_path)
    try:
        conn.execute(_DELETE_SQL, (block_id,))
        conn.commit()
    finally:
        conn.close()
