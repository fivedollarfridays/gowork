"""Action plan data models."""

from enum import Enum

from pydantic import BaseModel, Field


class ActionCategory(str, Enum):
    JOB_APPLICATION = "job_application"
    BENEFITS_ENROLLMENT = "benefits_enrollment"
    CREDIT_REPAIR = "credit_repair"
    CRIMINAL_RECORD = "criminal_record"
    TRAINING = "training"
    CAREER_CENTER = "career_center"
    HOUSING = "housing"
    CHILDCARE = "childcare"


class ActionItem(BaseModel):
    category: ActionCategory
    title: str
    detail: str | None = None
    priority: int = 0
    source_module: str
    resource_name: str | None = None
    resource_phone: str | None = None
    resource_address: str | None = None


class TimelinePhase(BaseModel):
    phase_id: str
    label: str
    start_day: int
    end_day: int
    actions: list[ActionItem] = Field(default_factory=list)


class ActionPlan(BaseModel):
    assessment_date: str
    phases: list[TimelinePhase]
    total_actions: int
