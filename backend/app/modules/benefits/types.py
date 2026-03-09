import logging
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

VALID_PROGRAMS = frozenset({
    "SNAP", "TANF", "Medicaid", "ALL_Kids",
    "Childcare_Subsidy", "Section_8", "LIHEAP",
})

ProgramName = Literal[
    "SNAP", "TANF", "Medicaid", "ALL_Kids",
    "Childcare_Subsidy", "Section_8", "LIHEAP",
]


class CliffSeverity(str, Enum):
    """Severity of a benefits cliff drop."""

    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class CliffType(str, Enum):
    """How a benefit phases out."""

    GRADUAL = "gradual"
    HARD = "hard"


class BenefitsProfile(BaseModel):
    """Household benefits profile for cliff analysis."""

    household_size: int = Field(default=1, ge=1, le=8)
    current_monthly_income: float = Field(default=0.0, ge=0)
    enrolled_programs: list[str] = Field(default_factory=list)
    dependents_under_6: int = Field(default=0, ge=0)
    dependents_6_to_17: int = Field(default=0, ge=0)
    state: str = "AL"

    @field_validator("enrolled_programs")
    @classmethod
    def validate_programs(cls, v: list[str]) -> list[str]:
        """Filter out unrecognized program names with a warning."""
        valid = [p for p in v if p in VALID_PROGRAMS]
        invalid = [p for p in v if p not in VALID_PROGRAMS]
        if invalid:
            logger.warning("Ignoring unrecognized programs: %s", invalid)
        return valid


class ProgramBenefit(BaseModel):
    """Benefit status for a single program at a given income level."""

    program: str
    monthly_value: float
    eligible: bool
    phase_out_start: float  # annual income where benefit begins reducing
    phase_out_end: float  # annual income where benefit reaches $0
    cliff_type: CliffType  # "gradual" | "hard"


class WageStep(BaseModel):
    """Net income breakdown at a single wage level."""

    wage: float  # hourly wage
    gross_monthly: float
    benefits_total: float
    net_monthly: float


class CliffPoint(BaseModel):
    """A point where net income drops as wages increase."""

    hourly_wage: float
    annual_income: float
    net_monthly_income: float
    lost_program: str
    monthly_loss: float
    severity: CliffSeverity  # "mild" (<$50), "moderate" ($50-200), "severe" (>$200)


class CliffAnalysis(BaseModel):
    """Complete cliff analysis result for a household profile."""

    wage_steps: list[WageStep]
    cliff_points: list[CliffPoint]
    current_net_monthly: float
    programs: list[ProgramBenefit]
    worst_cliff_wage: float | None = None
    recovery_wage: float | None = None
