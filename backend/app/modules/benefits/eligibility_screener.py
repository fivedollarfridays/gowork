"""Benefits program eligibility screener — rule-based, not legal determination.

Checks all 7 Alabama benefit programs against a household profile and returns
eligibility status, confidence, income headroom, and estimated monthly value.
"""

from app.modules.benefits.application_data import get_application_info
from app.modules.benefits.eligibility_checks import PROGRAM_CHECKS
from app.modules.benefits.thresholds import MONTHS_PER_YEAR
from app.modules.benefits.types import (
    BenefitsEligibility,
    BenefitsProfile,
    ProgramEligibility,
)

DISCLAIMER = (
    "This is an estimate based on general program rules. "
    "Contact the Alabama Department of Human Resources (DHR) "
    "for an official eligibility determination."
)


def screen_benefits_eligibility(
    profile: BenefitsProfile,
) -> BenefitsEligibility:
    """Screen household against all Alabama benefit programs."""
    annual = profile.current_monthly_income * MONTHS_PER_YEAR
    hs = min(profile.household_size, 8)
    children = profile.dependents_under_6 + profile.dependents_6_to_17

    eligible: list[ProgramEligibility] = []
    ineligible: list[ProgramEligibility] = []

    for program, check_fn in PROGRAM_CHECKS.items():
        result = check_fn(annual, hs, children, profile)
        if result.eligible:
            result.application_info = get_application_info(program)
        (eligible if result.eligible else ineligible).append(result)

    total = round(sum(p.estimated_monthly_value for p in eligible), 2)
    return BenefitsEligibility(
        eligible_programs=eligible,
        ineligible_programs=ineligible,
        total_estimated_monthly=total,
        disclaimer=DISCLAIMER,
    )
