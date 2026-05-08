"""Reputation event recording API (T24.7).

One endpoint — ``POST /api/listings/{listing_id}/events`` — appends a
single signal-rate event to ``listing_reputation_events``. Gated by
``any_of_roles("case_manager", "admin")``: case managers record
placements they witness, admins record manual events. Anonymous
session_id is permitted in the payload so events tied to anonymous
candidates are not lost.

The route is intentionally narrow: a single POST with a Pydantic body
and a try/except that translates the ``ValueError`` raised by
:func:`app.core.queries_listings_reputation.record_event` for an
unknown listing into a clean 404. Schema-level validation (the
``kind`` enum) is done by Pydantic ``Literal`` so FastAPI auto-emits
422 — the route layer does not re-validate.

Lives in its own module — NOT in ``auth.py`` — because ``auth.py`` is
already at 314/400 lines and adding a new route there would push the
file toward the 400-line ceiling without architectural reason. The
S23 ``assessments_review`` module is the precedent for split-out
role-gated endpoints.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import queries_listings_reputation
from app.core.auth_roles import any_of_roles
from app.core.database import get_db


router = APIRouter(prefix="/api/listings", tags=["listing-reputation"])


_RECORDER_ROLES = ("case_manager", "admin")
_require_recorder = any_of_roles(*_RECORDER_ROLES)


class EventBody(BaseModel):
    """Request body for ``POST /{listing_id}/events``.

    ``kind`` is a closed enum mirroring
    :data:`app.core.listings_verification_schema.EVENT_KINDS`; an
    unknown value is rejected at the Pydantic layer so FastAPI returns
    422 without the route layer ever seeing the request.

    ``session_id`` is optional and may carry the anonymous candidate
    session that the event applies to — anonymous sessions never have
    an account, so the event would otherwise lose its candidate-side
    anchor. ``recorded_by`` is NEVER taken from the body — it always
    comes from the authenticated gw_account cookie.
    """

    kind: Literal["response_received", "withdrawn", "placed", "ghosted"]
    session_id: str | None = None
    notes: str | None = None


@router.post("/{listing_id}/events")
async def record_event_endpoint(
    listing_id: int,
    body: EventBody,
    db: AsyncSession = Depends(get_db),
    account: dict = Depends(_require_recorder),
) -> dict:
    """Append one reputation event for *listing_id*.

    Returns ``{"event_id": <int>}`` on success.

    404 when the listing does not exist —
    :func:`queries_listings_reputation.record_event` raises
    ``ValueError`` for an unknown listing FK and the route translates
    it so the caller sees a clean status code instead of the dialect's
    raw FK / CHECK constraint error.
    """
    try:
        event_id = await queries_listings_reputation.record_event(
            db,
            listing_id=listing_id,
            event_kind=body.kind,
            recorded_by=account["id"],
            session_id=body.session_id,
            notes=body.notes,
        )
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    return {"event_id": event_id}


__all__ = ["router", "EventBody", "record_event_endpoint"]
