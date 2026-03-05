"""POST /api/credit/assess — Thin proxy to credit assessment API (/v1/assess/simple)."""

import httpx
from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.modules.credit.types import CreditAssessmentResult, SimpleCreditRequest

router = APIRouter(prefix="/api/credit", tags=["credit"])


def _check_credit_response(resp: httpx.Response) -> None:
    """Raise HTTPException if the credit API returned a non-200 response."""
    if resp.status_code == 200:
        return
    try:
        detail = resp.json().get("detail", "Credit API error")
    except Exception:
        detail = f"Credit API error (HTTP {resp.status_code})"
    raise HTTPException(status_code=resp.status_code, detail=detail)


@router.post("/assess")
async def assess_credit(profile: SimpleCreditRequest) -> CreditAssessmentResult:
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
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Credit assessment service unavailable. Ensure it's running on the configured port.",
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
    return resp.json()
