from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.modules.feedback.types import ResourceHealth


class BarrierType(str, Enum):
    CREDIT = "credit"
    TRANSPORTATION = "transportation"
    CHILDCARE = "childcare"
    HOUSING = "housing"
    HEALTH = "health"
    TRAINING = "training"
    CRIMINAL_RECORD = "criminal_record"


class BarrierSeverity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EmploymentStatus(str, Enum):
    UNEMPLOYED = "unemployed"
    UNDEREMPLOYED = "underemployed"
    SEEKING_CHANGE = "seeking_change"


class AvailableHours(str, Enum):
    DAYTIME = "daytime"
    EVENING = "evening"
    NIGHT = "night"
    FLEXIBLE = "flexible"


class ScheduleConstraints(BaseModel):
    available_days: list[str] = Field(
        default_factory=lambda: ["monday", "tuesday", "wednesday", "thursday", "friday"]
    )
    available_hours: AvailableHours = AvailableHours.DAYTIME


class AssessmentRequest(BaseModel):
    zip_code: str = Field(..., pattern=r"^361\d{2}$", description="Montgomery area zip (361xx)")
    employment_status: EmploymentStatus
    barriers: dict[BarrierType, bool]  # validated against BarrierType enum keys
    work_history: str = Field(..., max_length=500)
    target_industries: list[str] = Field(default_factory=list)
    has_vehicle: bool = False
    schedule_constraints: ScheduleConstraints = Field(default_factory=ScheduleConstraints)


class UserProfile(BaseModel):
    session_id: str
    zip_code: str
    employment_status: EmploymentStatus
    barrier_count: int
    primary_barriers: list[BarrierType]
    barrier_severity: BarrierSeverity
    needs_credit_assessment: bool
    transit_dependent: bool
    schedule_type: str
    work_history: str
    target_industries: list[str]


class Resource(BaseModel):
    id: int
    name: str
    category: str
    subcategory: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    phone: Optional[str] = None
    url: Optional[str] = None
    eligibility: Optional[str] = None
    services: Optional[list[str]] = None
    notes: Optional[str] = None
    health_status: ResourceHealth = ResourceHealth.HEALTHY


class MatchBucket(str, Enum):
    STRONG = "strong"
    POSSIBLE = "possible"
    AFTER_REPAIR = "after_repair"


class JobMatch(BaseModel):
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    transit_accessible: bool = False
    route: Optional[str] = None
    credit_check_required: str = "unknown"
    eligible_now: bool = True
    eligible_after: Optional[str] = None


class ScoredJobMatch(JobMatch):
    relevance_score: float = Field(ge=0.0, le=1.0)
    match_reason: str = ""
    bucket: MatchBucket = MatchBucket.POSSIBLE


class TransitConnection(BaseModel):
    route_number: int
    route_name: str
    connects_to: list[str]
    schedule: str  # e.g. "Mon-Sat 5am-9pm, no Sunday"


class BarrierCard(BaseModel):
    type: BarrierType
    severity: BarrierSeverity
    title: str
    timeline_days: Optional[int] = None
    actions: list[str]
    resources: list[Resource] = Field(default_factory=list)
    transit_matches: list[TransitConnection] = Field(default_factory=list)


class ReEntryPlan(BaseModel):
    plan_id: str
    session_id: str
    resident_summary: Optional[str] = None  # AI-generated narrative (Tier 4)
    barriers: list[BarrierCard]
    job_matches: list[JobMatch]  # flat list (backward compat)
    strong_matches: list[ScoredJobMatch] = Field(default_factory=list)
    possible_matches: list[ScoredJobMatch] = Field(default_factory=list)
    immediate_next_steps: list[str]
    credit_readiness_score: Optional[int] = None  # 0-100 (from credit API)
    eligible_now: list[str] = Field(default_factory=list)
    eligible_after_repair: list[str] = Field(default_factory=list)
    wioa_eligibility: Optional["WIOAEligibility"] = None


class DislocatedWorkerStatus(str, Enum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    NEEDS_VERIFICATION = "needs_verification"


class EligibilityConfidence(str, Enum):
    LIKELY = "likely"
    CONFIRMED = "confirmed"
    UNLIKELY = "unlikely"


class WIOAEligibility(BaseModel):
    """WIOA program eligibility screening result."""

    adult_program: bool
    adult_reasons: list[str]
    supportive_services: bool
    ita_training: bool
    dislocated_worker: DislocatedWorkerStatus
    confidence: EligibilityConfidence
