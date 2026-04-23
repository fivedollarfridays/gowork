"""Outcome tracking types -- Pydantic models for N+1 intelligence.

Records barrier resolution outcomes, plan follow-through, and resource
effectiveness. These signals aggregate into community intelligence that
improves recommendations for the next person.

Zero LLM calls. Fully deterministic.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


_UUID_RE = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"


class OutcomeSignalType(str, Enum):
    """Types of outcome signals the system tracks."""

    BARRIER_RESOLVED = "barrier_resolved"
    PLAN_FOLLOWED = "plan_followed"
    RESOURCE_EFFECTIVE = "resource_effective"


class BarrierOutcome(BaseModel):
    """Outcome for a single barrier resolution attempt."""

    barrier_id: str = Field(min_length=1)
    resolved: bool = False
    weeks_to_resolve: Optional[int] = Field(default=None, ge=0)


class OutcomeRecord(BaseModel):
    """Full outcome record submitted by a user after following their plan."""

    session_id: str = Field(pattern=_UUID_RE)
    signal_type: str
    barrier_outcomes: list[BarrierOutcome] = Field(default_factory=list)
    plan_accuracy: Optional[int] = Field(default=None, ge=1, le=5)
    resource_ratings: dict[str, bool] = Field(default_factory=dict)
    city: str = ""
    # ISO-8601 UTC timestamp. Optional on input so callers can let the
    # tracker auto-populate it; the DB-backed tracker always writes a
    # non-null value.
    created_at: Optional[str] = None


class BarrierInsight(BaseModel):
    """Aggregate insight for a single barrier type."""

    barrier_id: str
    resolution_count: int = 0
    avg_weeks_to_resolve: float = 0.0
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)


class CommunityInsights(BaseModel):
    """Aggregate outcome intelligence for a city."""

    total_outcomes: int = 0
    barrier_insights: list[BarrierInsight] = Field(default_factory=list)
    avg_plan_accuracy: float = 0.0
    city: str = ""
