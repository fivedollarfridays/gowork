"""Health check models."""

from typing import Literal
from pydantic import BaseModel


class HealthStatus(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    uptime_seconds: float
    llm_provider: str | None = None


class ServiceCheck(BaseModel):
    name: str
    status: Literal["up", "down", "unknown"]
    latency_ms: float | None = None
    error: str | None = None


class ReadinessStatus(BaseModel):
    ready: bool
    checks: list[ServiceCheck]


class LivenessStatus(BaseModel):
    alive: bool
    uptime_seconds: float
