"""Admin endpoint for runtime feature-flag toggles (T12.0b).

``POST /api/admin/flags/{name}`` toggles a named feature flag at runtime,
writes an audit row, enforces a per-actor rate limit (10/hour), and logs a
warning when enabling the PII-sensitive ``ENABLE_AI_GENERATION`` flag.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.auth import require_admin_key
from app.core.feature_flags import (
    _check_rate_limit,
    hash_actor_token,
    set_flag_runtime,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/flags", tags=["admin"])

_AI_FLAG = "ENABLE_AI_GENERATION"
_AI_WARNING = (
    "AI generation enables LLM processing of worker PII — verify data "
    "processing agreement is active"
)


class FlagToggleRequest(BaseModel):
    """Request body for POST /api/admin/flags/{name}."""

    enabled: bool
    reason: str = Field(..., min_length=1, max_length=500)


def _client_ip(request: Request) -> str:
    """Best-effort source-IP extraction for audit records."""
    if request.client is not None and request.client.host:
        return request.client.host
    return "unknown"


def _enforce_rate_limit(actor_hash: str) -> None:
    """Raise 429 if the actor has exceeded the per-hour toggle quota."""
    if not _check_rate_limit(actor_hash):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded: max 10 toggles per hour per admin token",
        )


def _apply_toggle(
    name: str, body: FlagToggleRequest, actor_token: str, source_ip: str,
) -> dict:
    """Apply the runtime toggle, emit the AI warning if applicable, and audit."""
    if name == _AI_FLAG and body.enabled:
        logger.warning(_AI_WARNING)
    try:
        return set_flag_runtime(
            flag_name=name,
            enabled=body.enabled,
            reason=body.reason,
            actor_token=actor_token,
            source_ip=source_ip,
        )
    except Exception:
        logger.exception("Failed to toggle feature flag %s", name)
        raise HTTPException(status_code=500, detail="Flag toggle failed") from None


@router.post("/{name}")
async def toggle_feature_flag(
    name: str,
    body: FlagToggleRequest,
    request: Request,
    x_admin_key: str = Header(...),
    _: None = Depends(require_admin_key),
) -> dict:
    """Toggle a feature flag at runtime and write an audit row.

    ``require_admin_key`` has already validated the header; we re-read it
    here so the handler can hash it for the audit trail.
    """
    actor_hash = hash_actor_token(x_admin_key)
    _enforce_rate_limit(actor_hash)
    summary = _apply_toggle(name, body, x_admin_key, _client_ip(request))
    logger.info(
        "Feature flag toggled: name=%s enabled=%s actor_hash=%s",
        name, body.enabled, actor_hash[:12],
    )
    return summary
