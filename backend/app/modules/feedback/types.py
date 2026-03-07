"""Feedback module types — Pydantic models and enums."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ResourceHealth(str, Enum):
    HEALTHY = "healthy"
    WATCH = "watch"
    FLAGGED = "flagged"
    HIDDEN = "hidden"


_UUID_RE = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"


class ResourceFeedbackRequest(BaseModel):
    resource_id: int = Field(ge=1)
    session_id: str = Field(pattern=_UUID_RE)
    helpful: bool
    barrier_type: Optional[str] = None
    token: str


class ResourceFeedbackResponse(BaseModel):
    success: bool
    resource_id: int
    helpful: bool


class VisitFeedbackRequest(BaseModel):
    token: str
    made_it_to_center: int = Field(ge=0, le=2)
    outcomes: list[str] = Field(default_factory=list, max_length=20)
    plan_accuracy: int = Field(ge=1, le=3)
    free_text: Optional[str] = Field(default=None, max_length=1000)


class VisitFeedbackResponse(BaseModel):
    success: bool
