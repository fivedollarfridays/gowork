"""Appointments API router (T12.10).

Nine endpoints under ``/api/appointments`` for worker-appointment CRUD
and status transitions. Every endpoint validates a session-scoped
``token`` query parameter against the ``feedback_tokens`` table and
enforces session ownership for appointment-id paths (403 on
cross-session access).

Status changes go through dedicated endpoints (``/attended``,
``/missed``, ``DELETE``) so the underlying scheduler emits the right
event. ``PATCH`` rejects ``status`` in the body with 400.

File intentionally delegates most non-HTTP logic to
:mod:`app.routes._appointments_helpers` to stay under the arch
12-functions-per-file limit.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict

from app.modules.appointments import scheduler
from app.modules.appointments.barrier_linker import auto_generate_placeholders
from app.modules.appointments.status_transitions import InvalidStatusTransition
from app.modules.appointments.types import Appointment
from app.modules.pathway.types import PathwayResult
from app.routes import _appointments_helpers as _h

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


def _resolve_db_path() -> str:
    """Indirection so tests can monkeypatch the DB path in one place."""
    return _h.resolve_db_path()


_PATCH_FORBIDDEN_FIELDS = ("status", "session_id", "id", "source")


class AppointmentPatch(BaseModel):
    """PATCH body — non-status fields only (status uses dedicated endpoints).

    Extra fields are allowed at parse time so the handler can return a
    400 (business-rule violation) for ``status`` / identity mutations
    rather than a generic 422 schema error.
    """

    model_config = ConfigDict(extra="allow")

    title: str | None = None
    starts_at: str | None = None
    ends_at: str | None = None
    location_name: str | None = None
    location_address: str | None = None
    notes: str | None = None


# -------------------- List / create --------------------


@router.get("", response_model=list[Appointment])
def list_appointments(
    session_id: str = Query(...),
    token: str = Query(...),
) -> list[Appointment]:
    """Return every appointment attached to a session (scheduler-ordered)."""
    db_path = _resolve_db_path()
    _h.verify_token(db_path, session_id, token)
    return scheduler.list_by_session(session_id, db_path=db_path)


@router.post("", response_model=Appointment, status_code=201)
def create_appointment(
    appointment: Appointment,
    token: str = Query(...),
) -> Appointment:
    """Insert a new appointment and emit ``appointment.created``."""
    db_path = _resolve_db_path()
    _h.verify_token(db_path, appointment.session_id, token)
    try:
        return scheduler.create(
            appointment.session_id, appointment, db_path=db_path,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# -------------------- Upcoming + from-pathway --------------------


@router.get("/upcoming", response_model=list[Appointment])
def list_upcoming(
    session_id: str = Query(...),
    token: str = Query(...),
    days: int = Query(7, ge=1, le=365),
) -> list[Appointment]:
    """Appointments scheduled within the next N days for this session."""
    db_path = _resolve_db_path()
    _h.verify_token(db_path, session_id, token)
    return scheduler.list_upcoming(session_id, days=days, db_path=db_path)


@router.post("/from-pathway", response_model=list[Appointment])
def create_from_pathway(
    session_id: str = Query(...),
    token: str = Query(...),
    city: str | None = Query(None),
) -> list[Appointment]:
    """(Re)seed placeholder appointments from the session's barrier list.

    Idempotent: returns ``[]`` when every eligible barrier already has
    a matching placeholder. Workers can call this on demand to restore
    placeholders that were manually deleted.
    """
    db_path = _resolve_db_path()
    _h.verify_token(db_path, session_id, token)
    barriers = _h.fetch_session_barriers(db_path, session_id)
    pathway = PathwayResult(
        pathways=[], current_wage=0.0, current_net_monthly=0.0,
        barriers_active=barriers,
    )
    resolved_city = city or _h.fetch_session_city(db_path, session_id)
    return auto_generate_placeholders(
        session_id, pathway, city=resolved_city, db_path=db_path,
    )


# -------------------- Single-appointment endpoints --------------------


@router.get("/{appointment_id}", response_model=Appointment)
def get_appointment(
    appointment_id: int, token: str = Query(...),
) -> Appointment:
    """Return one appointment. 404 if missing, 403 if owned by another session."""
    db_path = _resolve_db_path()
    session_id = _h.resolve_session_from_token(db_path, token)
    return _h.load_owned_appointment(
        appointment_id, session_id, db_path=db_path,
    )


@router.patch("/{appointment_id}", response_model=Appointment)
def patch_appointment(
    appointment_id: int, patch: AppointmentPatch, token: str = Query(...),
) -> Appointment:
    """Update non-status fields. 400 when body includes forbidden fields."""
    db_path = _resolve_db_path()
    session_id = _h.resolve_session_from_token(db_path, token)
    _h.load_owned_appointment(appointment_id, session_id, db_path=db_path)
    changes = _patch_to_changes(patch)
    if not changes:
        return _h.load_owned_appointment(
            appointment_id, session_id, db_path=db_path,
        )
    try:
        return scheduler.update(appointment_id, db_path=db_path, **changes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _patch_to_changes(patch: AppointmentPatch) -> dict[str, Any]:
    """Pydantic body -> scheduler.update kwargs; rejects forbidden fields.

    PATCH must not mutate status (use dedicated endpoints) nor identity
    fields. Forbidden fields raise 400 rather than the Pydantic-default
    422 so the contract is transparent to API callers.
    """
    raw = patch.model_dump(exclude_unset=True)
    for field in _PATCH_FORBIDDEN_FIELDS:
        if field in raw:
            raise HTTPException(
                status_code=400,
                detail=f"field '{field}' cannot be changed via PATCH",
            )
    return {k: v for k, v in raw.items() if v is not None}


@router.delete("/{appointment_id}", status_code=204)
def delete_appointment(
    appointment_id: int, token: str = Query(...),
) -> Response:
    """Soft-cancel an appointment (status=cancelled). Emits an event."""
    db_path = _resolve_db_path()
    session_id = _h.resolve_session_from_token(db_path, token)
    _h.load_owned_appointment(appointment_id, session_id, db_path=db_path)
    try:
        scheduler.cancel(appointment_id, db_path=db_path)
    except InvalidStatusTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return Response(status_code=204)


@router.post("/{appointment_id}/attended", response_model=Appointment)
def mark_attended(
    appointment_id: int, token: str = Query(...),
) -> Appointment:
    """Transition appointment -> attended. 409 if transition invalid."""
    return _transition(appointment_id, token, target="attended")


@router.post("/{appointment_id}/missed", response_model=Appointment)
def mark_missed(
    appointment_id: int, token: str = Query(...),
) -> Appointment:
    """Transition appointment -> missed. 409 if transition invalid."""
    return _transition(appointment_id, token, target="missed")


def _transition(
    appointment_id: int, token: str, *, target: str,
) -> Appointment:
    """Shared logic for the two status-transition endpoints."""
    db_path = _resolve_db_path()
    session_id = _h.resolve_session_from_token(db_path, token)
    _h.load_owned_appointment(appointment_id, session_id, db_path=db_path)
    action = scheduler.mark_attended if target == "attended" else scheduler.mark_missed
    try:
        return action(appointment_id, db_path=db_path)
    except InvalidStatusTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
