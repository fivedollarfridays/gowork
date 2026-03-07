"""Authentication dependencies."""

import hmac

from fastapi import Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.queries_feedback import token_exists, validate_token


async def require_session_token(
    db: AsyncSession, session_id: str, token: str,
) -> None:
    """Validate that token is valid and belongs to the given session.

    Raises 401 for invalid/expired tokens, 403 for session mismatch.
    """
    owner = await validate_token(db, token)
    if owner is None:
        if await token_exists(db, token):
            raise HTTPException(status_code=401, detail="Token expired")
        raise HTTPException(status_code=401, detail="Invalid token")
    if owner != session_id:
        raise HTTPException(status_code=403, detail="Token does not match session")


async def require_admin_key(x_admin_key: str = Header(...)) -> None:
    """Validate the X-Admin-Key header against the configured admin API key.

    Returns 503 when admin_api_key is not configured (empty).
    Returns 403 when the provided key doesn't match.
    FastAPI returns 422 automatically when the header is missing.
    """
    settings = get_settings()
    if not settings.admin_api_key:
        raise HTTPException(status_code=503, detail="Admin API key not configured")
    if not hmac.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(status_code=403, detail="Invalid admin key")
