"""Career Center Package data models."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from app.modules.matching.types import WIOAEligibility


class CareerCenterInfo(BaseModel):
    name: str
    phone: str
    address: str
    hours: str
    transit_route: str


class DocumentChecklistItem(BaseModel):
    label: str
    required: bool


class StaffSummary(BaseModel):
    employment_goal: str
    barrier_profile: list[str]
    wioa_eligibility: Optional[WIOAEligibility] = None
    staff_next_steps: list[str]


class ResidentActionPlan(BaseModel):
    document_checklist: list[DocumentChecklistItem]
    work_history: str
    what_to_say: list[str]
    what_to_expect: list[str]
    career_center: CareerCenterInfo
    programs: list[str]
    action_timeline: list[dict] = Field(default_factory=list)


class CreditPathway(BaseModel):
    blocking: list[str]
    not_blocking: list[str]
    dispute_steps: list[str]
    free_resources: list[str]


class CareerCenterPackage(BaseModel):
    staff_summary: StaffSummary
    resident_plan: ResidentActionPlan
    credit_pathway: Optional[CreditPathway] = None
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
