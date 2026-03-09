"""Feedback module types — Pydantic models and enums."""

import unicodedata
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("outcomes")
    @classmethod
    def validate_outcome_length(cls, v: list[str]) -> list[str]:
        for item in v:
            if len(item) > 100:
                raise ValueError("Outcome items must be 100 characters or fewer")
        return v

    @field_validator("free_text", mode="before")
    @classmethod
    def sanitize_free_text(cls, v: str | None) -> str | None:
        """MED-5: Sanitize free_text — strip, NFC-normalize, remove null bytes."""
        if v is None:
            return None
        v = v.strip()
        v = v.replace("\x00", "")
        v = unicodedata.normalize("NFC", v)
        return v or None


class VisitFeedbackResponse(BaseModel):
    success: bool
