"""Admin feedback inbox + flagged-resource queue routes (T26.3).

Five endpoints under ``/api/admin/feedback/...``, all gated by
:func:`require_role("admin")` (S22 cookie pattern):

* ``GET    /flagged?city=<slug>``                         — flagged-resource queue.
* ``POST   /flagged/{resource_id}/approve``               — clear flag (→ healthy).
* ``POST   /flagged/{resource_id}/confirm-hide``          — soft-hide (→ hidden).
* ``GET    /visits?reviewed=<bool>&limit=<n>&offset=<n>`` — visit-feedback inbox.
* ``POST   /visits/{id}/mark-reviewed``                   — flip reviewed + stamp.

This module is *additive*: it ships in a new file rather than extending
``routes/feedback.py`` because that one is candidate-facing (token-gated).
The new admin surfaces share zero auth code with the candidate surface;
mixing them would obscure the trust boundary.

T26.2 owns the ``routes/__init__.py`` registration that mounts this
router on the production app — single-owner shared-file edit this wave.
Tests in :mod:`tests.test_admin_feedback` mount the router on a fresh
:class:`fastapi.FastAPI` so they don't depend on T26.2 landing first.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import queries_admin_feedback
from app.core.auth_roles import require_role
from app.core.database import get_db


router = APIRouter(prefix="/api/admin/feedback", tags=["admin", "feedback"])

_require_admin = require_role("admin")


class MarkReviewedBody(BaseModel):
    """Optional body for ``POST /visits/{id}/mark-reviewed``.

    ``action_taken`` is a short free-text note recording the operator's
    follow-up (e.g. "called the case manager"). Stored verbatim on
    ``visit_feedback.action_taken``; surfaced back to the inbox so the
    list view shows what was done.
    """

    action_taken: str | None = Field(default=None, max_length=500)


@router.get("/flagged")
async def list_flagged(
    city: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _account: dict = Depends(_require_admin),
) -> dict:
    """Return the flagged-resource queue.

    Each item carries the resource's identifying columns plus a
    ``recent_negative_feedback`` list (last 30 days, newest-first).
    Optional ``?city=<slug>`` scopes to one city.
    """
    items = await queries_admin_feedback.list_flagged_resources(
        db, city=city
    )
    return {"items": items}


@router.post("/flagged/{resource_id}/approve")
async def approve_flagged(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    _account: dict = Depends(_require_admin),
) -> dict:
    """Approve a flagged resource — set ``health_status='healthy'``.

    Returns 404 if the resource does not exist; otherwise echoes the
    new ``health_status`` so the UI can update without a refetch.
    """
    updated = await queries_admin_feedback.set_resource_health(
        db, resource_id, "healthy"
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Resource not found")
    return {"id": resource_id, "health_status": "healthy"}


@router.post("/flagged/{resource_id}/confirm-hide")
async def confirm_hide_flagged(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    _account: dict = Depends(_require_admin),
) -> dict:
    """Confirm-hide a flagged resource — set ``health_status='hidden'``.

    Soft-delete: the row stays in the table so audit trails (feedback
    rows that reference it) remain intact. T26.2's restore endpoint
    reverses this (back to ``healthy``).
    """
    updated = await queries_admin_feedback.set_resource_health(
        db, resource_id, "hidden"
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Resource not found")
    return {"id": resource_id, "health_status": "hidden"}


@router.get("/visits")
async def list_visits(
    reviewed: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _account: dict = Depends(_require_admin),
) -> dict:
    """Paginated browse of the visit-feedback inbox.

    Filters:
      * ``reviewed=true`` — only reviewed rows.
      * ``reviewed=false`` — only unreviewed rows.
      * (omitted) — both.

    Limit is hard-capped at 100 (FastAPI ``le=100`` returns 422 above
    that). Default page size 50; offset returned in the response so
    the UI can render "showing N–M of total" without recomputing.
    """
    rows, total = await queries_admin_feedback.list_visit_feedback(
        db, reviewed=reviewed, limit=limit, offset=offset,
    )
    return {
        "items": rows,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/visits/{visit_id}/mark-reviewed")
async def mark_visit_reviewed(
    visit_id: int,
    body: MarkReviewedBody | None = None,
    db: AsyncSession = Depends(get_db),
    _account: dict = Depends(_require_admin),
) -> dict:
    """Flip ``reviewed=1`` on *visit_id* and stamp optional action.

    Empty body is allowed — sets ``reviewed=1`` and leaves
    ``action_taken`` NULL. Returns the updated columns so the UI
    can update the row in place. 404 when *visit_id* does not exist.
    """
    action_taken = body.action_taken if body is not None else None
    updated = await queries_admin_feedback.mark_visit_feedback_reviewed(
        db, visit_id, action_taken
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Visit feedback not found")
    return updated


__all__ = ["router", "MarkReviewedBody"]
