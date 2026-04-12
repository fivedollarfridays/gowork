"""Share plan routes — create and retrieve shared plan links."""

import json
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.cities.config import get_city_config
from app.core.audit import audit_log, get_client_ip
from app.core.auth import require_session_token
from app.core.database import get_db
from app.core.queries import get_session_by_id
from app.core.rate_limit import RateLimiter, require_rate_limit
from app.modules.feedback.tokens import generate_token

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


def _extract_career_center(plan_data: dict) -> tuple[str, str]:
    """Extract career center name and phone from plan or city config."""
    city = get_city_config()
    return city.name, city.state


@router.get("/shared/{share_token}")
async def get_shared_plan(
    share_token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Retrieve a shared plan by token. Public endpoint (no auth required)."""
    now = datetime.now(timezone.utc).isoformat()

    # Look up token
    result = await db.execute(
        text(
            "SELECT token, session_id, created_at, expires_at "
            "FROM share_tokens WHERE token = :tok"
        ),
        {"tok": share_token},
    )
    row = result.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Share link not found")

    token_val, session_id, created_at, expires_at = row
    if expires_at <= now:
        raise HTTPException(status_code=410, detail="Share link has expired")

    # Fetch the session plan
    session_row = await get_session_by_id(db, session_id)
    if session_row is None or not session_row.get("plan"):
        raise HTTPException(status_code=404, detail="Plan no longer available")

    plan_data = json.loads(session_row["plan"]) if isinstance(session_row["plan"], str) else session_row["plan"]
    barriers_raw = session_row.get("barriers", "[]")
    barriers = json.loads(barriers_raw) if isinstance(barriers_raw, str) else barriers_raw

    return {
        "session_id": session_id,
        "created_at": created_at,
        "barriers": barriers,
        "next_steps": _extract_next_steps(plan_data),
        "career_center_name": get_city_config().name,
        "career_center_phone": "",
    }
