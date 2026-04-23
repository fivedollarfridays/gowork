"""Appointment CRUD with status-machine validation and event emission (T12.7).

Public surface:
    create, get, list_by_session, list_upcoming,
    update, mark_attended, mark_missed, cancel, reschedule.

Persistence is delegated to `persistence.py`; transition rules live in
`status_transitions.py`. Every state-changing operation ends with an
`events.emit(...)` call — this module never imports its consumers so
the coupling stays one-way (aligns with the pub/sub layering guide).

Overlap detection (`_check_overlap`) is advisory: it logs a warning
when a new / rescheduled appointment clashes with an existing one for
the same session. It never blocks — soft signal only.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.core import events
from app.modules.appointments import persistence
from app.modules.appointments.status_transitions import check_transition
from app.modules.appointments.types import Appointment
from app.modules.common.temporal_types import AppointmentStatus

logger = logging.getLogger(__name__)


def _require(appointment_id: int, db_path: str | Path) -> Appointment:
    existing = persistence.select_by_id(appointment_id, db_path=db_path)
    if existing is None:
        raise ValueError(f"appointment {appointment_id} not found")
    return existing


def _check_overlap(
    session_id: str,
    starts_at: datetime | None,
    ends_at: datetime | None,
    *,
    exclude_id: int = 0,
    db_path: str | Path,
) -> None:
    """Emit a WARNING log if another appointment overlaps. Never raises."""
    if starts_at is None or ends_at is None:
        return
    clashes = persistence.select_overlapping(
        session_id, starts_at, ends_at,
        exclude_id=exclude_id, db_path=db_path,
    )
    if clashes:
        ids = [c.id for c in clashes]
        logger.warning(
            "Overlapping appointments for session %s: conflicts with %s",
            session_id, ids,
        )


def create(
    session_id: str, appointment: Appointment, *, db_path: str | Path,
) -> Appointment:
    """INSERT the appointment, emit `appointment.created`."""
    if appointment.session_id != session_id:
        raise ValueError("appointment.session_id must match session_id arg")
    _check_overlap(
        session_id, appointment.starts_at, appointment.ends_at,
        db_path=db_path,
    )
    stored = persistence.insert(appointment, db_path=db_path)
    events.emit("appointment.created", stored.model_dump(mode="json"))
    return stored


def get(
    appointment_id: int, *, db_path: str | Path,
) -> Appointment | None:
    return persistence.select_by_id(appointment_id, db_path=db_path)


def list_by_session(
    session_id: str, *, db_path: str | Path,
) -> list[Appointment]:
    return persistence.select_by_session(session_id, db_path=db_path)


def list_upcoming(
    session_id: str, days: int, *, db_path: str | Path,
) -> list[Appointment]:
    """Return future-scheduled appointments within `days` from now."""
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=days)
    out: list[Appointment] = []
    for appt in list_by_session(session_id, db_path=db_path):
        if appt.starts_at is None:
            continue
        if now <= appt.starts_at <= cutoff:
            out.append(appt)
    return out


def _transition_and_save(
    appointment_id: int,
    new_status: AppointmentStatus,
    *,
    db_path: str | Path,
) -> Appointment:
    """Validate the status transition, UPDATE, and return the new row."""
    current = _require(appointment_id, db_path)
    check_transition(current.status, new_status)
    persistence.update_fields(
        appointment_id, {"status": new_status.value}, db_path=db_path,
    )
    return _require(appointment_id, db_path)


def mark_attended(
    appointment_id: int, *, db_path: str | Path,
) -> Appointment:
    updated = _transition_and_save(
        appointment_id, AppointmentStatus.ATTENDED, db_path=db_path,
    )
    events.emit("appointment.attended", updated.model_dump(mode="json"))
    return updated


def mark_missed(
    appointment_id: int, *, db_path: str | Path,
) -> Appointment:
    updated = _transition_and_save(
        appointment_id, AppointmentStatus.MISSED, db_path=db_path,
    )
    events.emit("appointment.missed", updated.model_dump(mode="json"))
    return updated


def cancel(
    appointment_id: int, *, db_path: str | Path,
) -> Appointment:
    updated = _transition_and_save(
        appointment_id, AppointmentStatus.CANCELLED, db_path=db_path,
    )
    events.emit("appointment.cancelled", updated.model_dump(mode="json"))
    return updated


def reschedule(
    appointment_id: int,
    new_starts_at: datetime,
    new_ends_at: datetime,
    *,
    db_path: str | Path,
) -> Appointment:
    """Move the appointment to a new window; preserve old starts_at in notes."""
    current = _require(appointment_id, db_path)
    check_transition(current.status, AppointmentStatus.RESCHEDULED)
    _check_overlap(
        current.session_id, new_starts_at, new_ends_at,
        exclude_id=appointment_id, db_path=db_path,
    )
    old_iso = current.starts_at.isoformat() if current.starts_at else "unknown"
    history = f"rescheduled from {old_iso}"
    merged_notes = f"{current.notes}\n{history}" if current.notes else history
    persistence.update_fields(
        appointment_id,
        {
            "starts_at": new_starts_at.isoformat(),
            "ends_at": new_ends_at.isoformat(),
            "status": AppointmentStatus.RESCHEDULED.value,
            "notes": merged_notes,
        },
        db_path=db_path,
    )
    updated = _require(appointment_id, db_path)
    events.emit("appointment.rescheduled", updated.model_dump(mode="json"))
    return updated


def update(
    appointment_id: int,
    *,
    db_path: str | Path,
    **changes,
) -> Appointment:
    """Generic update. Validates status if that field is changing.

    For status changes, prefer the dedicated mark_* / cancel / reschedule
    helpers — they emit the right event. This helper skips emission
    because generic updates don't map onto a single event type.
    """
    current = _require(appointment_id, db_path)
    new_status = changes.get("status")
    if new_status is not None and new_status != current.status:
        check_transition(current.status, new_status)
        changes["status"] = new_status.value
    persistence.update_fields(appointment_id, changes, db_path=db_path)
    return _require(appointment_id, db_path)


__all__ = [
    "cancel",
    "create",
    "get",
    "list_by_session",
    "list_upcoming",
    "mark_attended",
    "mark_missed",
    "reschedule",
    "update",
]
