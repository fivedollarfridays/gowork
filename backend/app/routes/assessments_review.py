"""Reviewer queue API for the assessment authoring pipeline (T23.4).

Three endpoints under ``/api/admin/assessments`` mounted in the
project router registry. All three are gated by ``any_of_roles(
case_manager, sme_reviewer, dao_reviewer)`` — admins use the
shared admin tier (T23.5 publish endpoint) rather than this
reviewer-specific surface.

Routes:

* ``GET    /pending``                 — track-aware reviewer queue.
* ``GET    /{version_id}``            — full version + questions.
* ``POST   /{version_id}/review``     — record a review action.

State-machine guards live in :mod:`app.core.queries_assessments`
(via :mod:`app.core._assessments_state`); ``ValueError`` raised by
``record_review`` (e.g. attempting to review a published or retired
version) is translated to ``409 Conflict`` so the route never
swallows or rewrites state-machine semantics.

Reviewer-role inference for the queue filter
--------------------------------------------
``list_pending_reviews`` accepts a single ``reviewer_role`` and
applies the ``ROLE_TRACK_FILTER`` table. We pick the *most
permissive* role the caller holds among ``sme_reviewer >
case_manager / dao_reviewer`` — sme sees the union, the others see
their own track plus generic. If a single account holds multiple
narrow roles (rare) the broader sme filter wins.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import queries_assessments, queries_roles
from app.core.auth_roles import any_of_roles
from app.core.database import get_db


router = APIRouter(prefix="/api/admin/assessments", tags=["assessments-review"])


_REVIEWER_ROLES = ("case_manager", "sme_reviewer", "dao_reviewer")
_require_reviewer = any_of_roles(*_REVIEWER_ROLES)


class ReviewBody(BaseModel):
    """Request body for ``POST /{version_id}/review``.

    ``action`` is constrained to the three values the queries layer
    accepts; anything else is rejected with FastAPI's standard 422.
    ``comment`` is optional — short-text rationale recorded with the
    review row for the audit trail.
    """

    action: Literal["approve", "reject", "request_revision"]
    comment: str | None = None


async def _pick_reviewer_role(
    db: AsyncSession, account_id: int
) -> str:
    """Pick the broadest reviewer role held by *account_id*.

    sme_reviewer wins (union of all tracks) so a multi-role caller
    sees every track they are entitled to review. Falls back to
    case_manager / dao_reviewer; one of the three is guaranteed
    because the route is gated by :func:`any_of_roles` over those.
    """
    if await queries_roles.account_has_role(db, account_id, "sme_reviewer"):
        return "sme_reviewer"
    for role in ("case_manager", "dao_reviewer"):
        if await queries_roles.account_has_role(db, account_id, role):
            return role
    # Defensive fallback — should never hit because of the dep gate.
    return "case_manager"


@router.get("/pending")
async def list_pending(
    db: AsyncSession = Depends(get_db),
    account: dict = Depends(_require_reviewer),
) -> list[dict]:
    """Return draft / in_review versions visible to the caller.

    Track filter is derived from the account's reviewer role —
    sme_reviewer sees every track; case_manager sees vocational +
    generic; dao_reviewer sees dao_tech + generic.
    """
    role = await _pick_reviewer_role(db, account["id"])
    return await queries_assessments.list_pending_reviews(
        db, reviewer_role=role
    )


@router.get("/{version_id}")
async def get_version(
    version_id: int,
    db: AsyncSession = Depends(get_db),
    account: dict = Depends(_require_reviewer),
) -> dict:
    """Return one version + its questions for reviewer inspection.

    404 if the version does not exist. Payload includes
    ``rubric_json`` per question — internal reviewer surface only.
    """
    payload = await queries_assessments.get_version_with_questions(
        db, version_id
    )
    if payload is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return payload


@router.post("/{version_id}/review")
async def submit_review(
    version_id: int,
    body: ReviewBody,
    db: AsyncSession = Depends(get_db),
    account: dict = Depends(_require_reviewer),
) -> dict:
    """Record one review action on *version_id*.

    Returns ``{"review_id": <int>}`` on success. Returns 409 if the
    version is in an immutable status (published / retired) — this
    is the route translation of ``ValueError`` raised by
    :func:`queries_assessments.record_review`.
    """
    try:
        review_id = await queries_assessments.record_review(
            db,
            version_id=version_id,
            reviewer_id=account["id"],
            action=body.action,
            comment=body.comment,
        )
    except ValueError as err:
        raise HTTPException(status_code=409, detail=str(err)) from err
    return {"review_id": review_id}


__all__ = ["router", "ReviewBody"]
