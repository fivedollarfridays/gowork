"""POST /api/credit/assess — Thin proxy to credit assessment API (/v1/assess/simple)."""

import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.audit import audit_log, get_client_ip
from app.core.config import get_settings
from app.core.rate_limit import RateLimiter, require_rate_limit
from app.modules.credit.types import CreditAssessmentResult, SimpleCreditRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/credit", tags=["credit"])

_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
_check_rate = require_rate_limit(_rate_limiter)


def _check_credit_response(resp: httpx.Response) -> None:
    """Raise HTTPException if the credit API returned a non-200 response."""
    if resp.status_code == 200:
        return
    try:
        upstream_detail = resp.json().get("detail", resp.text[:200])
    except Exception:
        upstream_detail = resp.text[:200]
    logger.warning("Credit API error: status=%d detail=%s", resp.status_code, upstream_detail)
    raise HTTPException(status_code=502, detail="Credit assessment service error")


@router.post("/assess")
async def assess_credit(
    profile: SimpleCreditRequest,
    request: Request,
    _: None = Depends(_check_rate),
) -> CreditAssessmentResult:
    """Proxy to the credit assessment microservice's simple endpoint."""
    settings = get_settings()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.credit_api_url}/v1/assess/simple",
                json=profile.model_dump(),
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": settings.credit_api_key,
                },
            )
    except httpx.ConnectError as exc:
        logger.warning("Credit API connection error: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Credit assessment service unavailable",
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Credit assessment service timed out. Try again later.",
        )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=502,
            detail="Credit assessment network error. Try again later.",
        )
    _check_credit_response(resp)
    audit_log("credit_assessed", session_id="anonymous", client_ip=get_client_ip(request))
    return resp.json()
