"""Share plan routes — create and retrieve shared plan links."""

import json
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_log, get_client_ip
from app.core.auth import require_session_token
from app.core.database import get_db
from app.core.queries import get_session_by_id
from app.core.rate_limit import RateLimiter, require_rate_limit
from app.modules.common.temporal_types import coerce_to_aware_datetime
from app.modules.feedback.tokens import generate_token
from app.modules.matching.resource_router import get_career_center

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/plan", tags=["share"])

_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
_check_rate = require_rate_limit(_rate_limiter)

_SHARE_EXPIRY_DAYS = 7
_UUID_RE = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"


async def _create_share_token(db: AsyncSession, session_id: str) -> str:
    """Generate and persist a share token with 7-day expiry."""
    token = generate_token()
    now = datetime.now(timezone.utc)
    expires = (now + timedelta(days=_SHARE_EXPIRY_DAYS)).isoformat()
    await db.execute(
        text(
            "INSERT INTO share_tokens (token, session_id, created_at, expires_at) "
            "VALUES (:token, :sid, :created, :expires)"
        ),
        {"token": token, "sid": session_id, "created": now.isoformat(), "expires": expires},
    )
    await db.commit()
    return token


def _build_share_url(token: str) -> str:
    """Build the public share URL for a given token."""
    return f"/shared/{token}"


@router.post("/{session_id}/share")
async def create_share_link(
    session_id: str,
    request: Request,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_check_rate),
) -> dict:
    """Generate a shareable link for a session's plan."""
    await require_session_token(db, session_id, token)

    row = await get_session_by_id(db, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if not row.get("plan"):
        raise HTTPException(status_code=400, detail="No plan exists for this session")

    share_token = await _create_share_token(db, session_id)
    url = _build_share_url(share_token)

    audit_log("plan_shared", session_id=session_id, client_ip=get_client_ip(request))
    return {"share_token": share_token, "url": url}


def _extract_next_steps(plan_data: dict) -> list[str]:
    """Pull immediate next steps from plan JSON."""
    steps = plan_data.get("immediate_next_steps", [])
    if isinstance(steps, list):
        return steps[:10]
    return []


def _count_barriers(barriers_raw: object) -> int:
    """Return a non-PII scalar count of the worker's barriers.

    The raw barrier slugs (``criminal_record``, ``health``, ``housing``,
    ``credit``, ``childcare``) are protected-category PII under the same
    threat model as the compliance audit hashing (T13.59). The public share
    payload exposes only the count so a recipient can see "this person is
    working on N things" without learning *which* categories.
    """
    if isinstance(barriers_raw, str):
        try:
            barriers = json.loads(barriers_raw)
        except (json.JSONDecodeError, ValueError):
            return 0
    else:
        barriers = barriers_raw
    if isinstance(barriers, list):
        return len(barriers)
    if isinstance(barriers, dict):
        return len(barriers)
    return 0


def _resolve_career_center() -> tuple[str, str]:
    """Return (name, phone) for the active city's real career center.

    Falls back to ``("", "")`` if the resource router cannot resolve a center
    — the frontend handles empty strings; what we must avoid is the bare
    city name masquerading as a center (T13.72).
    """
    try:
        center = get_career_center()
    except (ImportError, AttributeError, KeyError):
        return "", ""
    return getattr(center, "name", "") or "", getattr(center, "phone", "") or ""


async def _load_active_share(
    db: AsyncSession, share_token: str,
) -> tuple[str, str]:
    """Look up + validate a share token. Return (session_id, created_at).

    Raises 404 if the token is unknown, 410 if expired.
    """
    result = await db.execute(
        text(
            "SELECT session_id, created_at, expires_at "
            "FROM share_tokens WHERE token = :tok"
        ),
        {"tok": share_token},
    )
    row = result.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Share link not found")

    session_id, created_at, expires_at = row
    # T13 stage-2 P1-2: parse the stored ISO timestamp into an aware
    # datetime instead of comparing strings lexically. Lexical compare is
    # only safe when both sides use the exact same offset spelling
    # (currently '+00:00'); a future migration writing 'Z' would silently
    # invert the comparison. ``coerce_to_aware_datetime`` accepts both
    # forms and naive datetimes the same way every other caller does.
    try:
        expires_at_dt = coerce_to_aware_datetime(expires_at)
    except (TypeError, ValueError):
        # Treat an unparseable timestamp as expired — fail-closed.
        raise HTTPException(status_code=410, detail="Share link has expired")
    if expires_at_dt <= datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Share link has expired")
    return session_id, created_at


@router.get("/shared/{share_token}")
async def get_shared_plan(
    share_token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Retrieve a shared plan by token. Public endpoint (no auth required).

    Public-safe payload only. Specifically excluded:
    - ``session_id`` (worker's persistent backend identifier — T13.71 P1)
    - raw ``barriers`` slug list (protected-category PII — T13.71 P1)

    Replaced with:
    - ``barriers_count``: non-identifying scalar so recipients still see that
      the worker is actively working on something, without learning *which*
      protected categories apply.
    """
    session_id, created_at = await _load_active_share(db, share_token)

    session_row = await get_session_by_id(db, session_id)
    if session_row is None or not session_row.get("plan"):
        raise HTTPException(status_code=404, detail="Plan no longer available")

    plan_raw = session_row["plan"]
    plan_data = json.loads(plan_raw) if isinstance(plan_raw, str) else plan_raw
    center_name, center_phone = _resolve_career_center()

    return {
        "created_at": created_at,
        "barriers_count": _count_barriers(session_row.get("barriers", "[]")),
        "next_steps": _extract_next_steps(plan_data),
        "career_center_name": center_name,
        "career_center_phone": center_phone,
    }
