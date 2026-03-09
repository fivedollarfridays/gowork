"""Transit-related types for schedule-aware matching."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TransitWarning(str, Enum):
    SUNDAY_GAP = "sunday_gap"
    NIGHT_GAP = "night_gap"
    LONG_WALK = "long_walk"
    TRANSFER_REQUIRED = "transfer_required"


class RouteFeasibility(BaseModel):
    """Transit route serving a location with schedule feasibility."""

    route_number: int
    route_name: str
    nearest_stop: str
    walk_miles: float
    first_bus: str  # e.g. "05:00"
    last_bus: str   # e.g. "21:00"
    has_sunday: bool = False
    feasible: bool


class TransitInfo(BaseModel):
    """Transit accessibility details for a job location."""

    serving_routes: list[RouteFeasibility] = Field(default_factory=list)
    transfer_count: int = 0
    warnings: list[TransitWarning] = Field(default_factory=list)
    google_maps_url: Optional[str] = None


class TransitConnection(BaseModel):
    route_number: int
    route_name: str
    connects_to: list[str]
    schedule: str  # e.g. "Mon-Sat 5am-9pm, no Sunday"
