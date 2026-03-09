"""WIOA eligibility types."""

from enum import Enum

from pydantic import BaseModel


class DislocatedWorkerStatus(str, Enum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    NEEDS_VERIFICATION = "needs_verification"


class WIOAConfidence(str, Enum):
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
    confidence: WIOAConfidence
