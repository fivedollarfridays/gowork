"""Admin claim-review dashboard routes (T24.9).

Four endpoints mounted under ``/api/employers/admin/claims/...`` —
all gated by ``require_role("admin")``:

* ``GET /pending`` — admin queue read; returns rows for verifications
  at the ``admin_reviewed`` tier (joined to claim + listing + employer).
* ``GET /{claim_id}`` — full claim+listing+employer+verification
  payload for the detail surface.
* ``POST /{claim_id}/approve`` — promote the employer to ``verified``;
  the verification tier stays at ``admin_reviewed`` (T24.9 spec —
  approval refreshes ``verified_at`` rather than escalating the tier).
* ``DELETE /{claim_id}`` — rejection; deletes the claim + verification
  rows and sets the employer's ``verification_status`` to ``retired``.

This module is split out of :mod:`app.routes.employers` (already at
its per-file size budget) so adding the four admin endpoints does not
push the issue/verify/intake module past the 400-line ceiling.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import queries_employers
from app.core.auth_roles import require_role
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/employers/admin/claims", tags=["employers", "admin"]
)


@router.get("/pending")
async def list_pending_claims(
    db: AsyncSession = Depends(get_db),
    _account: dict = Depends(require_role("admin")),
) -> list[dict]:
    """Admin queue: claims whose listing is at the ``admin_reviewed`` tier.

    Returns a list (possibly empty) of ``{claim_id, claimant_email,
    listing_id, listing_title, employer_account_id, employer_domain,
    verification_tier, ...}`` rows ordered by ``listing_claims.created_at``.
    """
    return await queries_employers.list_pending_admin_review(db)


@router.get("/{claim_id}")
async def get_claim(
    claim_id: int,
    db: AsyncSession = Depends(get_db),
    _account: dict = Depends(require_role("admin")),
) -> dict:
    """Detail payload for one claim — claim + listing + employer + verification.

    Returns 404 when the claim id does not exist.
    """
    detail = await queries_employers.get_claim_detail(db, claim_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="claim not found")
    return detail


@router.post("/{claim_id}/approve")
async def approve_claim(
    claim_id: int,
    db: AsyncSession = Depends(get_db),
    account: dict = Depends(require_role("admin")),
) -> dict:
    """Approve the admin-review claim; promote the employer to ``verified``.

    Returns ``{claim_id, employer_account_id, verification_status,
    verified_at}`` on success. 404 when the claim id does not exist.
    """
    result = await queries_employers.approve_admin_review(db, claim_id)
    if result is None:
        raise HTTPException(status_code=404, detail="claim not found")
    logger.info(
        "admin_claim_approved claim_id=%s admin_id=%s",
        claim_id, account.get("id"),
    )
    return result


@router.delete("/{claim_id}", status_code=204)
async def reject_claim(
    claim_id: int,
    db: AsyncSession = Depends(get_db),
    account: dict = Depends(require_role("admin")),
) -> Response:
    """Reject the admin-review claim — deletes claim + verification rows.

    Sets the employer's ``verification_status`` to ``retired``. Returns
    a 204 on success, 404 when the claim id does not exist.
    """
    deleted = await queries_employers.reject_admin_review(db, claim_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="claim not found")
    logger.info(
        "admin_claim_rejected claim_id=%s admin_id=%s",
        claim_id, account.get("id"),
    )
    return Response(status_code=204)


__all__ = ["router"]
