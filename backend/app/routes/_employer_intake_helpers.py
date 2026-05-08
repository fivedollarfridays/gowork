"""Helpers backing ``POST /api/employers/{eid}/listings/{lid}/intake`` (T24.5).

Lives next to :mod:`app.routes.employers` so the route handler can stay
inside the per-file size + function-count budgets on ``employers.py``.

The pieces here are:

* :class:`IntakeRequest` — the Pydantic body schema with field-level
  validation (non-empty must-haves / day-1 tasks; positive comp band
  with ``min <= max`` sanity guard).
* :func:`resolve_intake_caller` — the cookie-or-admin gate dependency.
  Resolves to the path's ``employer_account_id`` when EITHER the
  signed ``gw_employer_account`` cookie binds the caller to that same
  employer, OR the caller holds the ``admin`` role via the
  ``gw_account`` cookie. Anonymous callers and mismatched-employer
  callers both 403.
* :func:`execute_intake` — the orchestrator: verifies the listing
  belongs to the path employer (404 otherwise), persists the JSON
  blob via :func:`queries_listings_verification.set_intake`, and
  returns the updated verification row (intake_json INCLUDED — caller
  is the employer who just submitted it; this is the read-after-write
  surface).
"""

from __future__ import annotations

import json

from fastapi import Cookie, Depends, HTTPException, Path
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import queries_listings_verification
from app.core.database import get_db
from app.core.queries_roles import account_has_role
from app.routes._auth_claim_helpers import verify_account_cookie
from app.routes._employer_claim_helpers import (
    EMPLOYER_COOKIE_NAME,
    verify_employer_cookie,
)

# ``SESSION_COOKIE_NAME`` is duplicated here as a literal to avoid the
# transitive circular import that goes employers -> auth_claim_helpers
# -> ... ; the real source of truth is :mod:`._auth_claim_helpers`.
_SESSION_COOKIE_ALIAS = "gw_account"


# -------------------- Request schema --------------------


class IntakeRequest(BaseModel):
    """Structured intake answers for an employer-verified listing.

    All five list / scalar shape constraints fire as 422 before any DB
    hit. ``comp_band_min <= comp_band_max`` is enforced via a
    :func:`field_validator` on ``comp_band_max`` so the error message
    points at the load-bearing field.
    """

    must_haves: list[str] = Field(..., min_length=1)
    nice_to_haves: list[str] = Field(default_factory=list)
    real_day1_tasks: list[str] = Field(..., min_length=1)
    comp_band_min: int = Field(..., gt=0)
    comp_band_max: int = Field(..., gt=0)
    fair_chance_willingness: bool
    additional_notes: str | None = None

    @field_validator("must_haves", "real_day1_tasks", "nice_to_haves")
    @classmethod
    def _strip_empty_items(cls, v: list[str]) -> list[str]:
        for item in v:
            if not item or not item.strip():
                raise ValueError("list items must be non-empty strings")
        return v

    @field_validator("comp_band_max")
    @classmethod
    def _check_comp_band(cls, v: int, info) -> int:
        lo = info.data.get("comp_band_min")
        if lo is not None and v < lo:
            raise ValueError("comp_band_max must be >= comp_band_min")
        return v


# -------------------- Cookie-or-admin gate --------------------


async def _is_admin(db: AsyncSession, gw_account: str | None) -> bool:
    """Return True iff the signed gw_account cookie binds an admin account."""
    if not gw_account:
        return False
    account_id = verify_account_cookie(gw_account)
    if account_id is None:
        return False
    return await account_has_role(db, account_id, "admin")


async def resolve_intake_caller(
    employer_account_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    gw_employer_account: str | None = Cookie(
        default=None, alias=EMPLOYER_COOKIE_NAME
    ),
    gw_account: str | None = Cookie(
        default=None, alias=_SESSION_COOKIE_ALIAS
    ),
) -> int:
    """Authorise the caller against *employer_account_id*.

    Pass conditions (any one is sufficient):

    * Signed ``gw_employer_account`` cookie decodes to the same
      employer id as the path param (verified employer of record).
    * Caller holds the ``admin`` role via the ``gw_account`` cookie.

    Both gates raise a uniform 403 on failure — anonymous callers and
    mismatched-employer callers look identical from outside.
    """
    employer_id = verify_employer_cookie(gw_employer_account)
    if employer_id == employer_account_id:
        return employer_account_id
    if await _is_admin(db, gw_account):
        return employer_account_id
    raise HTTPException(status_code=403, detail="not_authorised")


# -------------------- Orchestrator --------------------


async def execute_intake(
    db: AsyncSession,
    *,
    employer_account_id: int,
    listing_id: int,
    body: IntakeRequest,
) -> dict:
    """Verify ownership, persist intake, and return the updated record.

    Returns the full verification row (intake_json INCLUDED — caller is
    the verified employer or an admin acting on their behalf, which
    is the read-after-write surface). Raises 404 when no verification
    row binds *listing_id* to *employer_account_id* (the listing
    either has no verification yet or is owned by a different employer
    — both look the same from the caller's perspective so we don't
    leak ownership).
    """
    existing = await queries_listings_verification.get_verification_for_listing(
        db, listing_id
    )
    if existing is None or int(existing["employer_account_id"]) != employer_account_id:
        raise HTTPException(
            status_code=404, detail="verification_not_found"
        )
    intake_json = json.dumps(body.model_dump(), separators=(",", ":"))
    await queries_listings_verification.set_intake(
        db, listing_id=listing_id, intake_json=intake_json
    )
    updated = await queries_listings_verification.get_verification_for_listing(
        db, listing_id
    )
    assert updated is not None  # set_intake just stamped it
    return dict(updated)


__all__ = [
    "IntakeRequest",
    "resolve_intake_caller",
    "execute_intake",
]
