"""SQLite persistence helpers for the appointments table (T12.7).

Kept out of `scheduler.py` so the scheduler stays under the project's
per-file function-count limit. Every function opens a short-lived
sqlite3 connection, operates, and closes — mirroring the pattern used
by `app.modules.outcomes.tracker`.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.modules.appointments.types import Appointment
from app.modules.common.temporal_types import AppointmentStatus, AppointmentType

_COLUMNS = (
    "id, session_id, type, title, starts_at, ends_at, location_name, "
    "location_address, barrier_link, status, source, notes, created_at"
)

_INSERT_SQL = (
    "INSERT INTO appointments "
    "(session_id, type, title, starts_at, ends_at, location_name, "
    "location_address, barrier_link, status, source, notes, created_at) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)

_SELECT_BY_ID_SQL = f"SELECT {_COLUMNS} FROM appointments WHERE id = ?"
_SELECT_BY_SESSION_SQL = (
    f"SELECT {_COLUMNS} FROM appointments WHERE session_id = ? "
    "ORDER BY starts_at ASC, id ASC"
)
_SELECT_OVERLAP_SQL = (
    f"SELECT {_COLUMNS} FROM appointments WHERE session_id = ? "
    "AND id != ? AND starts_at IS NOT NULL AND ends_at IS NOT NULL "
    "AND starts_at < ? AND ends_at > ?"
)


def _connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _row_to_appointment(row: tuple) -> Appointment:
    """Hydrate a DB row back into an Appointment model."""
    (
        rid, session_id, rtype, title, starts_at, ends_at,
        loc_name, loc_addr, barrier_link, status, source, notes, created_at,
    ) = row
    return Appointment(
        id=rid,
        session_id=session_id,
        type=AppointmentType(rtype),
        title=title,
        starts_at=_parse_iso(starts_at),
        ends_at=_parse_iso(ends_at),
        location_name=loc_name,
        location_address=loc_addr,
        barrier_link=barrier_link,
        status=AppointmentStatus(status),
        source=source or "user",
        notes=notes,
        created_at=_parse_iso(created_at),
    )


def _parse_iso(raw: str | None) -> datetime | None:
    if not raw:
        return None
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def insert(appointment: Appointment, *, db_path: str | Path) -> Appointment:
    """INSERT the appointment; return a copy with id + created_at populated."""
    created_at = appointment.created_at or datetime.now(timezone.utc)
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            _INSERT_SQL,
            (
                appointment.session_id,
                appointment.type.value,
                appointment.title,
                _iso(appointment.starts_at),
                _iso(appointment.ends_at),
                appointment.location_name,
                appointment.location_address,
                appointment.barrier_link,
                appointment.status.value,
                appointment.source,
                appointment.notes,
                _iso(created_at),
            ),
        )
        conn.commit()
        new_id = int(cur.lastrowid)
    finally:
        conn.close()
    return appointment.model_copy(update={"id": new_id, "created_at": created_at})


def select_by_id(
    appointment_id: int, *, db_path: str | Path
) -> Appointment | None:
    conn = _connect(db_path)
    try:
        row = conn.execute(_SELECT_BY_ID_SQL, (appointment_id,)).fetchone()
    finally:
        conn.close()
    return _row_to_appointment(row) if row else None


def select_by_session(
    session_id: str, *, db_path: str | Path
) -> list[Appointment]:
    conn = _connect(db_path)
    try:
        rows = conn.execute(_SELECT_BY_SESSION_SQL, (session_id,)).fetchall()
    finally:
        conn.close()
    return [_row_to_appointment(r) for r in rows]


def update_fields(
    appointment_id: int,
    changes: dict,
    *,
    db_path: str | Path,
) -> None:
    """UPDATE only the provided columns. Caller supplies pre-serialized values."""
    if not changes:
        return
    sets = ", ".join(f"{col} = ?" for col in changes)
    params = list(changes.values()) + [appointment_id]
    conn = _connect(db_path)
    try:
        conn.execute(
            f"UPDATE appointments SET {sets} WHERE id = ?", params,
        )
        conn.commit()
    finally:
        conn.close()


def select_overlapping(
    session_id: str,
    starts_at: datetime,
    ends_at: datetime,
    *,
    exclude_id: int = 0,
    db_path: str | Path,
) -> list[Appointment]:
    """Return appointments for the same session whose window overlaps.

    Overlap := existing.starts_at < new.ends_at AND existing.ends_at >
    new.starts_at. Excludes the row at `exclude_id` (used during update /
    reschedule to avoid matching self).
    """
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            _SELECT_OVERLAP_SQL,
            (session_id, exclude_id, _iso(ends_at), _iso(starts_at)),
        ).fetchall()
    finally:
        conn.close()
    return [_row_to_appointment(r) for r in rows]


__all__ = [
    "insert",
    "select_by_id",
    "select_by_session",
    "select_overlapping",
    "update_fields",
]
