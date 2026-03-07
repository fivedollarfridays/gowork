"""Admin authentication dependency."""

from fastapi import Header, HTTPException

from app.core.config import get_settings


async def require_admin_key(x_admin_key: str = Header(...)) -> None:
    """Validate the X-Admin-Key header against the configured admin API key.

    Returns 503 when admin_api_key is not configured (empty).
    Returns 403 when the provided key doesn't match.
    FastAPI returns 422 automatically when the header is missing.
    """
    settings = get_settings()
    if not settings.admin_api_key:
        raise HTTPException(status_code=503, detail="Admin API key not configured")
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")
