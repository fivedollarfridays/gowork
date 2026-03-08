"""Types for Job Readiness Score — mirrors Credit Readiness pattern."""

from enum import Enum

from pydantic import BaseModel, Field


class ReadinessBand(str, Enum):
    NOT_READY = "not_ready"
    DEVELOPING = "developing"
    READY = "ready"
    STRONG = "strong"


class ReadinessFactor(BaseModel):
    """Single scoring factor with weight and detail."""

    name: str
    weight: float = Field(ge=0.0, le=1.0)
    score: int = Field(ge=0, le=100)
    detail: str = ""


class ReadinessPathwayStep(BaseModel):
    """Actionable step toward job readiness."""

    step_number: int
    action: str
    resource: str = ""
    timeline_days: int = 0
    completed: bool = False


class JobReadinessResult(BaseModel):
    """Complete job readiness assessment — mirrors CreditAssessmentResult."""

    overall_score: int = Field(ge=0, le=100)
    readiness_band: ReadinessBand
    factors: list[ReadinessFactor]
    pathway: list[ReadinessPathwayStep] = Field(default_factory=list)
    estimated_days_to_ready: int = 0
    summary: str = ""
