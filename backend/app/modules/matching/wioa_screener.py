"""WIOA eligibility screener — rule-based heuristic, not legal determination."""

import re

from app.modules.matching.filters import CERT_DB
from app.modules.matching.types import BarrierType, UserProfile
from app.modules.matching.types_wioa import DislocatedWorkerStatus, WIOAConfidence, WIOAEligibility

# Barriers that independently qualify for WIOA Adult program
QUALIFYING_BARRIERS = {
    BarrierType.CREDIT,
    BarrierType.TRANSPORTATION,
    BarrierType.CHILDCARE,
    BarrierType.CRIMINAL_RECORD,
}

# Barriers that indicate supportive services eligibility
SUPPORTIVE_BARRIERS = {BarrierType.TRANSPORTATION, BarrierType.CHILDCARE}

# Certification pattern derived from filters.CERT_DB — single source of truth
_CERT_PATTERN = re.compile(r"\b(" + "|".join(CERT_DB.keys()) + r")\b", re.IGNORECASE)


def has_expired_certification(work_history: str) -> bool:
    """Check if work history mentions recognized certifications."""
    return bool(_CERT_PATTERN.search(work_history))


def screen_wioa_eligibility(profile: UserProfile) -> WIOAEligibility:
    """Screen user profile for likely WIOA program eligibility."""
    qualifying = [
        b.value for b in profile.primary_barriers if b in QUALIFYING_BARRIERS
    ]
    adult_eligible = len(qualifying) > 0

    has_supportive = any(
        b in SUPPORTIVE_BARRIERS for b in profile.primary_barriers
    )

    return WIOAEligibility(
        adult_program=adult_eligible,
        adult_reasons=qualifying,
        supportive_services=adult_eligible and has_supportive,
        ita_training=adult_eligible and has_expired_certification(profile.work_history),
        dislocated_worker=DislocatedWorkerStatus.NEEDS_VERIFICATION,
        confidence=WIOAConfidence.LIKELY,
    )
