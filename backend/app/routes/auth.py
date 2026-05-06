"""Authentication routes — magic-link issuance (T22.7).

Exposes ``POST /api/auth/magic-link``. The endpoint is deliberately
opaque to clients:

* Always returns ``202 Accepted`` with no body — whether the email is
  known, unknown, or rate-limited. This kills account-enumeration and
  prevents callers from inferring whether a send actually happened.
* Mints a ~256-bit URL-safe token via
  :func:`app.core.queries_accounts.mint_magic_link_credential`. Only
  the SHA-256 hash is persisted; the raw token is handed to SendGrid
  exactly once and discarded.
* Account-on-first-use: an unknown email is created transparently so
  the very first login still works.
* Rate-limited two ways: 3/hour per email and 10/hour per client IP.
  When over-limit, the call is logged and silently dropped (no email
  is sent) but the response is still 202.

The actual claim flow (token → session) lives in T22.8 — the validate
side mirrors :func:`mint_magic_link_credential` by hashing the input
and looking up the (credential_type, credential_value_hash) index.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import queries_accounts
from app.core.audit import get_client_ip
from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import RateLimiter
from app.integrations.email import send_transactional

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
