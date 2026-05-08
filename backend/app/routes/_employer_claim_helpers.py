"""Helpers backing ``GET /api/employers/claim/verify`` (T24.4).

Mirror of :mod:`app.routes._auth_claim_helpers` for the employer side.
Lives next to :mod:`app.routes.employers` so the verify handler can
stay inside the per-file size budget on ``employers.py``.

The pieces here are:

* HMAC-signed employer-identity cookie (``gw_employer_account``) —
  parallel to S22's ``gw_account`` but scoped to the employer side.
  Reuses :data:`Settings.audit_hash_salt` (no new secret) but signs a
  prefixed message so a ``gw_account`` value cannot satisfy the
  employer verifier and vice-versa.
* The pre-baked uniform-401 / 409 ``Response`` builders, kept here so
  the byte-identical claim-failure body has exactly one source of
  truth (oracle-prevention — same posture as S22 _auth_claim_helpers).
"""

from __future__ import annotations

import hmac
from datetime import datetime, timezone

from fastapi import Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import queries_employers, queries_listings_verification
from app.core._listings_verification_internals import hash_claim_token
from app.core.config import get_settings


EMPLOYER_COOKIE_NAME = "gw_employer_account"
_EMPLOYER_COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days
#: Distinct HMAC namespace so a ``gw_account`` cookie cannot satisfy
#: the employer verifier (cross-cookie confusion guard).
_COOKIE_PREFIX = "emp"

# Pre-encoded JSON bodies. Bytes (not dicts) so every failure response
# is byte-identical — eliminates any whitespace / key-order oracle.
_INVALID_TOKEN_BODY = b'{"detail":"invalid_or_expired_token"}'
_CONFLICT_BODY = b'{"detail":"listing_already_claimed"}'


def _sign_employer_id(employer_account_id: int) -> str:
    """HMAC-SHA256 hex of ``emp:{id}`` under :data:`audit_hash_salt`.

    Reusing ``audit_hash_salt`` rather than introducing a new secret
    inherits the existing operational guarantees (production validator
    rejects the default value) without expanding the rotation surface.
    The ``emp:`` prefix in the signed message scopes the HMAC to the
    employer identity so a leaked ``gw_account`` HMAC cannot be
    repurposed to forge an employer cookie (or vice-versa).
    """
    salt = get_settings().audit_hash_salt.encode("utf-8")
    msg = f"{_COOKIE_PREFIX}:{employer_account_id}".encode("utf-8")
    return hmac.new(salt, msg, "sha256").hexdigest()


def build_employer_cookie_value(employer_account_id: int) -> str:
    """Format the cookie value as ``emp:<id>:<hmac>``."""
    return (
        f"{_COOKIE_PREFIX}:{employer_account_id}:"
        f"{_sign_employer_id(employer_account_id)}"
    )


def verify_employer_cookie(value: str | None) -> int | None:
    """Return the employer id encoded in *value* iff the HMAC validates.

    Counterpart to :func:`build_employer_cookie_value`. Returns ``None``
    for any of:

    * value is missing, empty, or wrong shape,
    * id half is not a positive integer,
    * the HMAC does not match the expected signature for the id.

    Uses :func:`hmac.compare_digest` to keep the comparison constant-
    time so the validity check cannot be turned into a timing oracle
    on the secret.
    """
    if not value:
        return None
    parts = value.split(":", 2)
    if len(parts) != 3 or parts[0] != _COOKIE_PREFIX:
        return None
    raw_id, signature = parts[1], parts[2]
    try:
        employer_id = int(raw_id)
    except ValueError:
        return None
    if employer_id <= 0:
        return None
    expected = _sign_employer_id(employer_id)
    if not hmac.compare_digest(expected, signature):
        return None
    return employer_id


def set_employer_cookie(response: Response, employer_account_id: int) -> None:
    """Attach the signed employer cookie with safe defaults.

    Attributes mirror :func:`_auth_claim_helpers.set_account_cookie`:

    * ``HttpOnly`` — JS in the browser cannot read the cookie.
    * ``SameSite=Lax`` — sent on top-level navigations (the magic-link
      click is a top-level GET) but not on cross-site sub-requests.
    * ``Secure`` — only outside development so the dev server on plain
      http://localhost can still see the cookie.
    """
    secure = get_settings().environment != "development"
    response.set_cookie(
        key=EMPLOYER_COOKIE_NAME,
        value=build_employer_cookie_value(employer_account_id),
        max_age=_EMPLOYER_COOKIE_MAX_AGE,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


def invalid_token_response() -> Response:
    """Uniform 401 used for every verify-failure mode (no lifecycle oracle)."""
    return Response(
        status_code=401,
        content=_INVALID_TOKEN_BODY,
        media_type="application/json",
    )


def listing_conflict_response() -> Response:
    """409 returned when the listing is already verified by another employer."""
    return Response(
        status_code=409,
        content=_CONFLICT_BODY,
        media_type="application/json",
    )


# -------------------- Verify-flow DB helpers (T24.4) --------------------


async def resolve_verify_target(
    db: AsyncSession, *, claimant_email: str
) -> tuple[int, str] | None:
    """Return ``(employer_account_id, verification_tier)`` for *claimant_email*.

    Re-derives the employer-of-record from ``claimant_email`` (so the
    verify path is independent of any employer_account_id stored on
    the claim row — the T24.3 mint side may persist it as NULL).
    Reads ``employer_accounts.verification_status`` to pick the tier:
    ``admin_review`` → ``admin_reviewed``; otherwise ``claim_verified``.
    Returns None if the email's domain doesn't resolve to an employer
    (defensive — T24.3 always seeds one, but the verify path must not
    crash on a hand-crafted token).
    """
    domain = queries_listings_verification.extract_domain_from_email(
        claimant_email
    )
    if not domain:
        return None
    employer = await queries_employers.get_employer_by_domain(db, domain)
    if employer is None:
        return None
    status = str(employer["verification_status"])
    tier = "admin_reviewed" if status == "admin_review" else "claim_verified"
    return int(employer["id"]), tier


async def promote_employer_if_pending(
    db: AsyncSession, employer_account_id: int
) -> None:
    """Lift ``verification_status`` from ``pending`` to ``verified``.

    Skipped for ``admin_review`` (T24.9 admin must approve manually)
    and for any already-terminal status (``verified`` / ``retired``).
    Conditional UPDATE keeps the path idempotent: silent no-op when
    the row is no longer ``pending``.
    """
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        text(
            "UPDATE employer_accounts SET verification_status = 'verified', "
            "verified_at = :ts "
            "WHERE id = :id AND verification_status = 'pending'"
        ),
        {"id": employer_account_id, "ts": now},
    )
    await db.commit()


# -------------------- Verify orchestrator (T24.4) --------------------


async def _record_verification_or_conflict(
    db: AsyncSession,
    *,
    listing_id: int,
    employer_account_id: int,
    tier: str,
) -> Response | None:
    """Insert the verification row, returning a 409 Response on conflict.

    Wraps :func:`queries_listings_verification.create_verification` so
    the orchestrator can stay flat. ``ValueError`` from the query layer
    means the listing is already claimed by a *different* employer.
    """
    try:
        await queries_listings_verification.create_verification(
            db,
            listing_id=listing_id,
            employer_account_id=employer_account_id,
            tier=tier,
            verified_by=0,
        )
    except ValueError:
        return listing_conflict_response()
    return None


async def _finalize_verification(
    db: AsyncSession,
    *,
    listing_id: int,
    employer_account_id: int,
    tier: str,
    response: Response,
) -> dict | Response:
    """Write the verification row + promote employer + set cookie.

    Returns the success JSON body or a 409 ``Response`` if the listing
    is already verified by a different employer. The promote/cookie
    side-effects only run on the success leg.
    """
    conflict = await _record_verification_or_conflict(
        db,
        listing_id=listing_id,
        employer_account_id=employer_account_id,
        tier=tier,
    )
    if conflict is not None:
        return conflict
    await promote_employer_if_pending(db, employer_account_id)
    set_employer_cookie(response, employer_account_id)
    return {
        "employer_account_id": employer_account_id,
        "listing_id": listing_id,
        "verification_tier": tier,
        "next_step": "intake",
    }


async def execute_claim_verify(
    db: AsyncSession, *, raw_token: str, response: Response
) -> dict | Response:
    """End-to-end verify pipeline: validate, mark used, write, cookie.

    Returns the JSON success body (and side-effects *response* with the
    employer cookie) or a pre-baked uniform 401 / 409 ``Response``.
    Single-use across all outcomes — the credential is consumed even on
    409 (mirrors S22 magic-link claim's no-replay invariant).
    """
    token_hash = hash_claim_token(raw_token)
    claim = await queries_listings_verification.find_unused_claim_by_hash(
        db, token_hash=token_hash
    )
    if claim is None:
        return invalid_token_response()
    target = await resolve_verify_target(
        db, claimant_email=str(claim["claimant_email"])
    )
    await queries_listings_verification.mark_claim_used(
        db, int(claim["id"])
    )
    if target is None:
        return invalid_token_response()
    employer_account_id, tier = target
    return await _finalize_verification(
        db,
        listing_id=int(claim["listing_id"]),
        employer_account_id=employer_account_id,
        tier=tier,
        response=response,
    )


__all__ = [
    "EMPLOYER_COOKIE_NAME",
    "build_employer_cookie_value",
    "verify_employer_cookie",
    "set_employer_cookie",
    "invalid_token_response",
    "listing_conflict_response",
    "resolve_verify_target",
    "promote_employer_if_pending",
    "execute_claim_verify",
]
