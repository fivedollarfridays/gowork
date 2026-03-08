"""Health check endpoints."""

import time

from fastapi import APIRouter, Request, Response, status
from sqlalchemy import text

from app.core.database import get_engine
from app.health.models import (
    HealthStatus,
    LivenessStatus,
    ReadinessStatus,
    ServiceCheck,
)

router = APIRouter(prefix="/health", tags=["health"])

APP_START_TIME = time.time()
APP_VERSION = "0.1.0"


async def check_database() -> ServiceCheck:
    """Check database connectivity."""
    start = time.time()
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency = (time.time() - start) * 1000
        return ServiceCheck(name="database", status="up", latency_ms=latency)
    except Exception as e:
        return ServiceCheck(name="database", status="down", error=str(e))


def check_rag_store(request: Request) -> ServiceCheck:
    """Check if RAG store is loaded and ready."""
    try:
        store = getattr(request.app.state, "rag_store", None)
        if store is None:
            return ServiceCheck(name="rag_store", status="down", error="Not initialized")
        if not store.is_ready():
            return ServiceCheck(name="rag_store", status="down", error="Index not loaded")
        return ServiceCheck(name="rag_store", status="up", latency_ms=0)
    except Exception as e:
        return ServiceCheck(name="rag_store", status="down", error=str(e))


@router.get("/live", response_model=LivenessStatus)
async def liveness():
    """Liveness probe — is the application running?"""
    uptime = time.time() - APP_START_TIME
    return LivenessStatus(alive=True, uptime_seconds=uptime)


@router.get("/ready", response_model=ReadinessStatus)
async def readiness(request: Request, response: Response):
    """Readiness probe — can the application serve traffic?"""
    checks = [await check_database(), check_rag_store(request)]
    ready = all(check.status == "up" for check in checks)
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessStatus(ready=ready, checks=checks)


@router.get("", response_model=HealthStatus)
async def health():
    """General health check with version and uptime."""
    uptime = time.time() - APP_START_TIME
    try:
        db_check = await check_database()
        health_status = "healthy" if db_check.status == "up" else "degraded"
    except Exception:
        health_status = "unhealthy"
    return HealthStatus(status=health_status, version=APP_VERSION, uptime_seconds=uptime)
