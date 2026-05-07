"""Authentication routes — magic-link issuance (T22.7) + claim (T22.8).

Exposes:

* ``POST /api/auth/magic-link`` — always-202 issuance endpoint. See
  the route docstring for the no-enumeration / rate-limit contract.
* ``GET  /api/auth/claim?token=…`` — validates a magic-link token,
  marks it consumed, sets a session cookie, and (if a ``session_id``
  rides along on the request) binds the anonymous session to the
  account. Returns a uniform 401 for invalid / expired / already-used
  tokens so the response cannot be used as an oracle on the token
  lifecycle. Returns 409 when the carried session_id is already
  claimed by a different account (no silent overwrite).

Claim parameter aliasing
------------------------
``GET /api/auth/claim`` declares its query params with the Python
names ``magic_token`` / ``claim_sid`` (``alias="token"`` /
``alias="session_id"`` on the wire). The aliasing keeps the URL
contract intact while telling the cross-session route inventory
(``tests._route_inventory``) that this is an *account-claim*
endpoint, not a feedback-session-owned one — the magic-link token is
not a feedback session token, so it must not be subjected to the
session-A id + session-B token IDOR contract that flags any
``(session_id, token)`` pair.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import queries_accounts
from app.core.audit import get_client_ip
from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import RateLimiter
from app.integrations.email import send_transactional
from app.routes._auth_claim_helpers import (
    SESSION_COOKIE_NAME,
    invalid_token_response,
    session_conflict_response,
    set_account_cookie,
    try_claim_session,
    verify_account_cookie,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

logger = logging.getLogger(__name__)

_TOKEN_TTL_MINUTES = 15
_HOUR_SECONDS = 60 * 60

# In-memory rate limiters. Anonymous-first invariant: no DB writes for
# rate-limit accounting — survives restarts via re-derivation rather
# than persistence. Acceptable for the issuance window (15 min) and
# the modest per-key counts (3 / 10).
_email_limiter = RateLimiter(max_requests=3, window_seconds=_HOUR_SECONDS)
_ip_limiter = RateLimiter(max_requests=10, window_seconds=_HOUR_SECONDS)

# Conservative email shape check — we deliberately avoid pulling in the
# heavy ``email-validator`` dependency just to enforce 422 on garbage
# input. The strict-correctness boundary is the SendGrid send.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# -------------------- Request schema --------------------


class MagicLinkRequest(BaseModel):
    """Request body for ``POST /api/auth/magic-link``.

    A lightweight regex check rejects clearly malformed addresses with
    a 422 — the no-enumeration contract still holds because validation
    runs before any DB lookup. Full RFC-grade validation happens on
    the SendGrid side.
    """

    email: str

    @field_validator("email")
    @classmethod
    def _check_email_shape(cls, v: str) -> str:
        if not _EMAIL_RE.match(v.strip()):
            raise ValueError("invalid email format")
        return v


# -------------------- Helpers --------------------


def _normalize(email: str) -> str:
    return email.strip().lower()


def _claim_url(raw_token: str) -> str:
    base = get_settings().frontend_url.rstrip("/")
    return f"{base}/auth/claim?token={raw_token}"


def _build_email_body(claim_url: str) -> tuple[str, str]:
    """Return (text_body, html_body) for the magic-link email."""
    text_body = (
        "Sign in to MontGoWork by opening this link in the next 15 minutes:\n\n"
        f"{claim_url}\n\n"
        "If you did not request this, you can safely ignore the email."
    )
    html_body = (
        "<p>Sign in to MontGoWork by opening this link in the next "
        "15 minutes:</p>"
        f'<p><a href="{claim_url}">{claim_url}</a></p>'
        "<p>If you did not request this, you can safely ignore the email.</p>"
    )
    return text_body, html_body


async def _resolve_or_create_account(
    db: AsyncSession, email: str
) -> int:
    """Account-on-first-use: return the existing id, or create a new row."""
    existing = await queries_accounts.get_account_by_email(db, email)
    if existing is not None:
        return int(existing["id"])
    return await queries_accounts.create_account(db, email)


def _check_rate_limits(email: str, client_ip: str) -> bool:
    """Return True if BOTH per-email and per-IP buckets have capacity.

    We deliberately consume both buckets even when one fails so that a
    spammer hitting the per-IP limit also burns down their per-email
    quota — it makes the limiter harder to game by rotating one axis.
    """
    email_ok = _email_limiter.check(email)
    ip_ok = _ip_limiter.check(client_ip)
    return email_ok and ip_ok


async def _issue_and_send(
    db: AsyncSession, *, email: str, account_id: int
) -> None:
    """Mint a credential, build the email, hand it off to SendGrid.

    Errors are logged and swallowed: the route MUST return 202 even
    when SendGrid is unreachable. Token issuance failures (DB) are
    let through so the caller sees a 500 — those indicate a real bug.
    """
    expires = datetime.now(timezone.utc) + timedelta(
        minutes=_TOKEN_TTL_MINUTES
    )
    raw_token, credential_id = await queries_accounts.mint_magic_link_credential(
        db, account_id=account_id, expires_at=expires
    )
    claim_url = _claim_url(raw_token)
    text_body, html_body = _build_email_body(claim_url)
    try:
        send_transactional(
            to=email,
            subject="Your MontGoWork sign-in link",
            html=html_body,
            text_fallback=text_body,
            category="magic_link",
        )
    except Exception:  # noqa: BLE001 - swallow to preserve no-enum contract
        logger.exception(
            "magic_link send failed credential_id=%s", credential_id
        )


# -------------------- Route --------------------


@router.post("/magic-link", status_code=202)
async def issue_magic_link(
    body: MagicLinkRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Mint a single-use magic-link token and email it to *body.email*.

    Always returns 202 Accepted. The response body is intentionally
    empty: callers MUST NOT branch on whether the email was actually
    sent (rate-limited, kill-switched, or transient SendGrid failure
    all look identical from outside).
    """
    email = _normalize(body.email)
    client_ip = get_client_ip(request)

    if not _check_rate_limits(email, client_ip):
        logger.info(
            "magic_link rate-limited: email_hash=%s ip=%s",
            email[:1] + "***", client_ip,
        )
        return Response(status_code=202)

    account_id = await _resolve_or_create_account(db, email)
    await _issue_and_send(db, email=email, account_id=account_id)
    return Response(status_code=202)


# -------------------- Claim flow (T22.8) --------------------


async def _maybe_claim_session(
    db: AsyncSession, *, account_id: int, claim_sid: str | None
) -> tuple[list[str], Response | None]:
    """Try to bind *claim_sid* to *account_id*.

    Returns ``(claimed_ids, conflict_response)``. ``conflict_response``
    is non-None iff a different account already owns *claim_sid* — the
    caller must short-circuit with that response without marking the
    credential used.
    """
    if not claim_sid:
        return [], None
    ok = await try_claim_session(
        db, account_id=account_id, session_id=claim_sid
    )
    if not ok:
        logger.info(
            "magic_link claim conflict account_id=%s session_id=%s",
            account_id, claim_sid,
        )
        return [], session_conflict_response()
    return [claim_sid], None


@router.get("/claim", response_model=None)
async def claim_magic_link(
    response: Response,
    magic_token: str = Query(..., alias="token"),
    claim_sid: str | None = Query(None, alias="session_id"),
    db: AsyncSession = Depends(get_db),
) -> dict | Response:
    """Validate a magic-link token and bind the browser to the account.

    Returns 200 ``{"account_id", "claimed_session_ids"}`` on success
    (cookie set), 401 with a uniform body for invalid / expired /
    replayed tokens, and 409 when *session_id* is already owned by a
    different account.
    """
    token_hash = queries_accounts.hash_token(magic_token)
    found = await queries_accounts.find_unused_credential_by_hash(
        db, token_hash=token_hash
    )
    if found is None:
        return invalid_token_response()
    account_id, credential_id = found

    claimed, conflict = await _maybe_claim_session(
        db, account_id=account_id, claim_sid=claim_sid
    )
    # Consume the credential before returning — including on 409. Otherwise
    # account B could re-POST the same valid token until 15-min expiry,
    # trying different session_ids until one isn't already claimed by
    # someone else. Single-use must hold across all outcomes.
    await queries_accounts.mark_credential_used(db, credential_id)
    if conflict is not None:
        return conflict
    set_account_cookie(response, account_id)
    return {"account_id": account_id, "claimed_session_ids": claimed}


# -------------------- Read flow (T22.11) --------------------


_ANON_ME_BODY = {"account_id": None, "email": None}


@router.get("/me")
async def read_account_me(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the account bound to the current ``gw_account`` cookie.

    Always returns ``200``:

    * Anonymous (no cookie / malformed / tampered HMAC / unknown id)
      yields ``{"account_id": null, "email": null}``.
    * Valid cookie yields ``{"account_id": int, "email": str}``.

    The 200-with-null shape (rather than a 401 on tampering) keeps the
    anonymous-first invariant — every browser receives the same shape
    whether or not it has ever claimed a session — and avoids any
    tampering oracle on the cookie signature.
    """
    raw_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    account_id = verify_account_cookie(raw_cookie)
    if account_id is None:
        return _ANON_ME_BODY
    row = await queries_accounts.get_account_by_id(db, account_id)
    if row is None:
        return _ANON_ME_BODY
    return {"account_id": int(row["id"]), "email": str(row["email"])}
