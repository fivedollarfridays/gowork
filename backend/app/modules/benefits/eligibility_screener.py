"""Benefits program eligibility screener -- rule-based, not legal determination.

City-aware: uses benefits.router to select the correct program checks,
application data, and disclaimer for the active city.
"""

from app.modules.benefits.router import (
    get_application_info,
    get_program_checks,
    get_screener_disclaimer,
)
from app.modules.benefits.thresholds import MONTHS_PER_YEAR
from app.modules.benefits.types import (
    BenefitsEligibility,
    BenefitsProfile,
    ProgramEligibility,
)


def screen_benefits_eligibility(
    profile: BenefitsProfile,
) -> BenefitsEligibility:
    """Screen household against benefit programs for the active city."""
    annual = profile.current_monthly_income * MONTHS_PER_YEAR
    hs = min(profile.household_size, 8)
    children = profile.dependents_under_6 + profile.dependents_6_to_17

    program_checks = get_program_checks()
    disclaimer = get_screener_disclaimer()

    eligible: list[ProgramEligibility] = []
    ineligible: list[ProgramEligibility] = []

    for program, check_fn in program_checks.items():
        result = check_fn(annual, hs, children, profile)
        if result.eligible:
            result.application_info = get_application_info(program)
        (eligible if result.eligible else ineligible).append(result)

    total = round(sum(p.estimated_monthly_value for p in eligible), 2)
    return BenefitsEligibility(
        eligible_programs=eligible,
        ineligible_programs=ineligible,
        total_estimated_monthly=total,
        disclaimer=disclaimer,
    )
