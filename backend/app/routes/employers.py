"""Employer-side listing claim routes (T24.3).

``POST /api/employers/claim`` — always-202 issuance endpoint that mints
a single-use magic-link-style token tied to a listing and emails it to
the claimant. Mirrors the candidate-side magic-link no-enumeration
contract: validation runs before any DB write; unknown listing,
rate-limited, kill-switched, and SendGrid-failed callers all see the
same empty 202 as the happy path.

Trust posture: the endpoint is the OUTER door to verification
(T24.4/T24.5 will own the verify step). What this route decides is
the *target tier* via a domain heuristic — if the email domain
fuzzy-matches ``job_listings.company`` the auto-created
``employer_accounts`` row stays ``verification_status='pending'``
(T24.4 can lift to ``claim_verified``); otherwise the row is flagged
``admin_review`` so T24.4 routes into the admin-review tier.

Rate limits are tighter than candidate-side magic-link (5/IP + 3/email
vs 10 + 3): employer-side has a small valid sender population per
listing, so a high per-IP rate is almost always abuse.
"""

from __future__ import annotations

import logging
import re

from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import BaseModel, field_validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import queries_employers, queries_listings_verification
from app.core.audit import get_client_ip
from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import RateLimiter
from app.routes._employer_claim_helpers import execute_claim_verify
from app.routes._employer_issue_helpers import company_matches_domain

# Backward-compat alias — existing T24.3 tests import the heuristic via
# ``from app.routes.employers import _company_matches_domain``. The
# implementation moved to :mod:`._employer_issue_helpers` to keep this
# file inside the per-file size + function-count budgets.
_company_matches_domain = company_matches_domain

router = APIRouter(prefix="/api/employers", tags=["employers"])

logger = logging.getLogger(__name__)

_HOUR_SECONDS = 60 * 60

# In-memory rate limiters. Anonymous-first invariant + always-202
# contract: we never persist limiter state. Tighter buckets than the
# candidate-side magic-link issuance (5 IP / 3 email vs 10 / 3).
_email_limiter = RateLimiter(max_requests=3, window_seconds=_HOUR_SECONDS)
_ip_limiter = RateLimiter(max_requests=5, window_seconds=_HOUR_SECONDS)

# Conservative email shape check — mirror auth.py so 422 fires before
# any DB lookup. Full RFC validation is deferred to SendGrid.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# -------------------- Request schema --------------------


class ClaimRequest(BaseModel):
    """Body for ``POST /api/employers/claim``.

    A regex shape-check rejects malformed addresses with a 422 — the
    no-enumeration contract still holds because validation runs before
    any DB lookup. Full RFC validation happens on the SendGrid side.
    """

    listing_id: int
    claimant_email: str

    @field_validator("claimant_email")
    @classmethod
    def _check_email_shape(cls, v: str) -> str:
        if not _EMAIL_RE.match(v.strip()):
            raise ValueError("invalid email format")
        return v


# -------------------- Helpers --------------------


def _claim_url(raw_token: str) -> str:
    base = get_settings().frontend_url.rstrip("/")
    return f"{base}/employers/claim?token={raw_token}"


def _build_email_body(claim_url: str) -> tuple[str, str]:
    """Return (text_body, html_body) for the listing-claim email."""
    text_body = (
        "Confirm your employer claim on this MontGoWork listing by "
        "opening this link in the next 15 minutes:\n\n"
        f"{claim_url}\n\n"
        "If you did not request this, you can safely ignore the email.\n"
        "— Sent under the MontGoWork charter."
    )
    html_body = (
        "<p>Confirm your employer claim on this MontGoWork listing by "
        "opening this link in the next 15 minutes:</p>"
        f'<p><a href="{claim_url}">{claim_url}</a></p>'
        "<p>If you did not request this, you can safely ignore the email.</p>"
        "<p><em>Sent under the MontGoWork charter.</em></p>"
    )
    return text_body, html_body


async def _listing_company(
    db: AsyncSession, listing_id: int
) -> tuple[bool, str | None]:
    """Return ``(exists, company)`` for *listing_id* — single SELECT."""
    result = await db.execute(
        text("SELECT company FROM job_listings WHERE id = :lid"),
        {"lid": listing_id},
    )
    row = result.first()
    if row is None:
        return False, None
    return True, row._mapping["company"]


async def _resolve_employer_for_domain(
    db: AsyncSession, *, domain: str, company: str | None
) -> int:
    """Return the ``employer_accounts.id`` for *domain*, creating if absent.

    First-seen verification_status is ``pending`` when *company* fuzzy-
    matches *domain*, else ``admin_review`` so T24.4 verify routes the
    listing into the admin queue. Existing rows are returned as-is.
    """
    existing = await queries_employers.get_employer_by_domain(db, domain)
    if existing is not None:
        return int(existing["id"])
    new_id = await queries_employers.create_employer_account(
        db, name=domain, domain=domain
    )
    if not _company_matches_domain(company, domain):
        await db.execute(
            text(
                "UPDATE employer_accounts "
                "SET verification_status = 'admin_review' WHERE id = :id"
            ),
            {"id": new_id},
        )
        await db.commit()
    return new_id


def _check_rate_limits(email: str, client_ip: str) -> bool:
    """True iff both per-email and per-IP buckets have capacity.

    Both buckets are consumed even when one fails so a spammer hitting
    the per-IP limit also burns down the per-email quota — same idiom
    as :mod:`app.routes.auth`. Tighter caps because the employer-side
    valid sender population is small.
    """
    email_ok = _email_limiter.check(email)
    ip_ok = _ip_limiter.check(client_ip)
    return email_ok and ip_ok


async def _mint_and_send(
    db: AsyncSession, *, listing_id: int, email: str
) -> None:
    """Mint a claim credential and dispatch the email via SendGrid.

    SendGrid errors are logged + swallowed to preserve the 202 contract.
    """
    raw_token, claim_id = (
        await queries_listings_verification.mint_listing_claim_token(
            db,
            listing_id=listing_id,
            claimant_email=email,
            claimant_account_id=None,
        )
    )
    claim_url = _claim_url(raw_token)
    text_body, html_body = _build_email_body(claim_url)
    from app.integrations.email import send_transactional
    try:
        send_transactional(
            to=email,
            subject="Confirm your MontGoWork listing claim",
            html=html_body,
            text_fallback=text_body,
            category="listing_claim",
        )
    except Exception:  # noqa: BLE001 - swallow to preserve no-enum contract
        logger.exception(
            "listing_claim send failed claim_id=%s", claim_id
        )


async def _process_claim(
    db: AsyncSession, *, listing_id: int, email: str
) -> None:
    """Full pipeline: lookup listing, resolve employer, mint + send.

    Unknown listing → silent return so the 202 response shape is
    indistinguishable from the happy path (anti-enumeration).
    """
    exists, company = await _listing_company(db, listing_id)
    if not exists:
        return
    domain = queries_listings_verification.extract_domain_from_email(email)
    if not domain:
        return
    await _resolve_employer_for_domain(db, domain=domain, company=company)
    await _mint_and_send(db, listing_id=listing_id, email=email)


# -------------------- Route --------------------


@router.post("/claim", status_code=202)
async def issue_listing_claim(
    body: ClaimRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Mint a single-use listing-claim token and email it to *body.claimant_email*.

    Always returns 202 Accepted with an empty body. Callers MUST NOT
    branch on whether an email was actually sent: rate-limited,
    unknown-listing, kill-switched, and transient SendGrid failures
    all look identical from outside.
    """
    email = body.claimant_email.strip().lower()
    client_ip = get_client_ip(request)

    if not _check_rate_limits(email, client_ip):
        logger.info(
            "listing_claim rate-limited: email_hash=%s ip=%s",
            email[:1] + "***", client_ip,
        )
        return Response(status_code=202)

    await _process_claim(db, listing_id=body.listing_id, email=email)
    return Response(status_code=202)


# -------------------- Verify route (T24.4) --------------------


@router.get("/claim/verify", response_model=None)
async def verify_listing_claim(
    response: Response,
    raw_token: str = Query(..., alias="token"),
    db: AsyncSession = Depends(get_db),
) -> dict | Response:
    """Validate a claim token and bind the browser to the employer identity.

    Returns 200 ``{employer_account_id, listing_id, verification_tier,
    next_step}`` on success (cookie set), 401 (uniform body) for
    invalid / expired / replayed tokens, 409 when the listing is
    already verified by a *different* employer. Single-use across all
    outcomes (mirrors S22 magic-link claim). Business logic lives in
    :func:`_employer_claim_helpers.execute_claim_verify` so this file
    stays inside the per-file size budget.
    """
    return await execute_claim_verify(db, raw_token=raw_token, response=response)
