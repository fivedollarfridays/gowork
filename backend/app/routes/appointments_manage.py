"""Public (unauthenticated) manage-appointment endpoint (T12.10b).

Single route: ``GET /api/appointments/manage?token=...&action=...``.

Auth model
----------
No session / feedback token — authority comes from the signed
manage-appointment token in the query string. That token is minted
server-side and embedded in worker-facing emails (cancel / reschedule /
view CTAs). It is single-use (atomic INSERT into ``used_tokens``) and
carries a 7-day TTL by default.

Error-oracle defense
--------------------
Every failure mode (malformed, expired, action-mismatch, unknown aid,
replay) returns the same 401 body so an attacker cannot probe the
endpoint to enumerate appointment ids or distinguish failure types.
The single exception is a successful VIEW on a non-existent row, which
is physically unreachable — `verify()` already rejects unknown aids.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from app.modules.appointments import scheduler, tokens
from app.routes import _appointments_helpers as _h

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/appointments", tags=["appointments"])

_UNIFORM_401_DETAIL = "Invalid or expired manage-appointment token."


def _resolve_db_path() -> str:
    """Indirection so tests can monkeypatch the DB path in one place."""
    return _h.resolve_db_path()


def _verify_or_401(token: str, action: tokens.TokenAction, db_path: str) -> int:
    """Return the verified appointment id or raise uniform 401."""
    try:
        return tokens.verify(token, action, db_path=db_path)
    except tokens.TokenError:
        # Log at debug so operators can diagnose, but never leak to caller.
        logger.debug(
            "manage-token rejected: action=%s", action.value, exc_info=True,
        )
        raise HTTPException(status_code=401, detail=_UNIFORM_401_DETAIL) from None


@router.get("/manage")
def manage_appointment(
    token: str = Query(...),
    action: tokens.TokenAction = Query(...),
) -> dict:
    """Dispatch a signed manage-link action. Uniform 401 on any failure."""
    db_path = _resolve_db_path()
    appointment_id = _verify_or_401(token, action, db_path)
    if action == tokens.TokenAction.CANCEL:
        return _handle_cancel(appointment_id, db_path)
    if action == tokens.TokenAction.RESCHEDULE:
        return _handle_reschedule(appointment_id)
    return _handle_view(appointment_id, db_path)


def _handle_cancel(appointment_id: int, db_path: str) -> dict:
    """Transition to cancelled; fold any scheduler error into uniform 401."""
    try:
        scheduler.cancel(appointment_id, db_path=db_path)
    except (ValueError, Exception) as exc:  # noqa: BLE001 — uniform oracle
        logger.debug(
            "cancel failed for aid=%s: %s", appointment_id, exc,
        )
        raise HTTPException(
            status_code=401, detail=_UNIFORM_401_DETAIL,
        ) from None
    return {"appointment_id": appointment_id, "status": "cancelled"}


def _handle_reschedule(appointment_id: int) -> dict:
    """Return a redirect hint; actual reschedule UI is out of S12b scope."""
    return {
        "appointment_id": appointment_id,
        "redirect": f"/appointments/{appointment_id}/reschedule",
    }


def _handle_view(appointment_id: int, db_path: str) -> dict:
    """Return appointment details. Missing row -> uniform 401."""
    appt = scheduler.get(appointment_id, db_path=db_path)
    if appt is None:
        raise HTTPException(status_code=401, detail=_UNIFORM_401_DETAIL)
    return {"appointment": appt.model_dump(mode="json")}


__all__ = ["router"]
