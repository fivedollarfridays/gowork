"""Per-program eligibility check functions for Texas benefit programs."""

from app.modules.benefits.texas.program_calculators import PROGRAM_CALCULATORS
from app.modules.benefits.texas.thresholds import (
    AMI_FORT_WORTH_2026,
    CEAP_FPL_LIMIT_PCT,
    CHILDCARE_SMI_LIMIT_PCT,
    CHIP_FPL_PCT,
    FPL_2026,
    SECTION_8_AMI_LIMIT_PCT,
    SMI_2026,
    TANF_MAX_MONTHLY,
    MONTHS_PER_YEAR,
)
from app.modules.benefits.types import (
    BenefitsProfile,
    EligibilityConfidence,
    ProgramEligibility,
)

_NEAR_THRESHOLD_BAND = 0.10


def _confidence(annual: float, threshold: float) -> EligibilityConfidence:
    """Determine confidence based on distance from threshold."""
    if annual > threshold:
        return EligibilityConfidence.UNLIKELY
    if annual >= threshold * (1 - _NEAR_THRESHOLD_BAND):
        return EligibilityConfidence.POSSIBLE
    return EligibilityConfidence.LIKELY


def _benefit_value(program: str, annual: float, profile: BenefitsProfile) -> float:
    calc = PROGRAM_CALCULATORS.get(program)
    return calc(annual, profile) if calc else 0.0


def _check_snap(
    annual: float, hs: int, _children: int, profile: BenefitsProfile,
) -> ProgramEligibility:
    fpl = FPL_2026[hs]
    threshold = fpl * 1.30
    is_eligible = annual <= threshold
    return ProgramEligibility(
        program="SNAP",
        eligible=is_eligible,
        confidence=_confidence(annual, threshold),
        income_threshold=threshold,
        income_headroom=round(threshold - annual, 2),
        estimated_monthly_value=round(_benefit_value("SNAP", annual, profile), 2) if is_eligible else 0.0,
        reason="Income below 130% FPL" if is_eligible else "Income exceeds 130% FPL",
    )


def _check_tanf(
    annual: float, hs: int, _children: int, profile: BenefitsProfile,
) -> ProgramEligibility:
    max_benefit = TANF_MAX_MONTHLY.get(hs, 308)
    threshold = max_benefit * MONTHS_PER_YEAR * 0.75
    is_eligible = annual <= threshold
    return ProgramEligibility(
        program="TANF",
        eligible=is_eligible,
        confidence=_confidence(annual, threshold),
        income_threshold=threshold,
        income_headroom=round(threshold - annual, 2),
        estimated_monthly_value=round(max_benefit, 2) if is_eligible else 0.0,
        reason="Income below TANF limit" if is_eligible else "Income exceeds TANF limit",
    )


def _check_medicaid(
    _annual: float, _hs: int, _children: int, _profile: BenefitsProfile,
) -> ProgramEligibility:
    return ProgramEligibility(
        program="Medicaid",
        eligible=False,
        confidence=EligibilityConfidence.UNLIKELY,
        income_threshold=0,
        income_headroom=0,
        estimated_monthly_value=0.0,
        reason="Texas has not expanded Medicaid for adults. See CHIP for children.",
    )


def _check_chip(
    annual: float, hs: int, children: int, profile: BenefitsProfile,
) -> ProgramEligibility:
    fpl = FPL_2026[hs]
    threshold = fpl * CHIP_FPL_PCT
    if children == 0:
        return ProgramEligibility(
            program="CHIP",
            eligible=False,
            confidence=EligibilityConfidence.UNLIKELY,
            income_threshold=threshold,
            income_headroom=0,
            estimated_monthly_value=0.0,
            reason="No dependent children in household",
        )
    is_eligible = annual <= threshold
    return ProgramEligibility(
        program="CHIP",
        eligible=is_eligible,
        confidence=_confidence(annual, threshold),
        income_threshold=threshold,
        income_headroom=round(threshold - annual, 2),
        estimated_monthly_value=round(_benefit_value("CHIP", annual, profile), 2) if is_eligible else 0.0,
        reason=f"Income below 200% FPL with {children} child(ren)" if is_eligible else "Income exceeds 200% FPL",
    )


def _check_childcare(
    annual: float, hs: int, _children: int, profile: BenefitsProfile,
) -> ProgramEligibility:
    smi = SMI_2026[hs]
    threshold = smi * CHILDCARE_SMI_LIMIT_PCT
    if profile.dependents_under_6 == 0:
        return ProgramEligibility(
            program="Childcare_Subsidy",
            eligible=False,
            confidence=EligibilityConfidence.UNLIKELY,
            income_threshold=threshold,
            income_headroom=0,
            estimated_monthly_value=0.0,
            reason="No dependents under age 6",
        )
    is_eligible = annual <= threshold
    return ProgramEligibility(
        program="Childcare_Subsidy",
        eligible=is_eligible,
        confidence=_confidence(annual, threshold),
        income_threshold=threshold,
        income_headroom=round(threshold - annual, 2),
        estimated_monthly_value=round(_benefit_value("Childcare_Subsidy", annual, profile), 2) if is_eligible else 0.0,
        reason="Income below 85% SMI with children under 6" if is_eligible else "Income exceeds 85% SMI",
    )


def _check_section_8(
    annual: float, hs: int, _children: int, profile: BenefitsProfile,
) -> ProgramEligibility:
    ami = AMI_FORT_WORTH_2026[hs]
    threshold = ami * SECTION_8_AMI_LIMIT_PCT
    is_eligible = annual <= threshold
    reason = (
        "Income below 50% AMI; typical waitlist is 1-3 years"
        if is_eligible
        else "Income exceeds 50% AMI"
    )
    return ProgramEligibility(
        program="Section_8",
        eligible=is_eligible,
        confidence=_confidence(annual, threshold),
        income_threshold=threshold,
        income_headroom=round(threshold - annual, 2),
        estimated_monthly_value=round(_benefit_value("Section_8", annual, profile), 2) if is_eligible else 0.0,
        reason=reason,
    )


def _check_ceap(
    annual: float, hs: int, children: int, profile: BenefitsProfile,
) -> ProgramEligibility:
    fpl = FPL_2026[hs]
    threshold = fpl * CEAP_FPL_LIMIT_PCT
    is_eligible = annual <= threshold
    reason = (
        "Income below 150% FPL; seasonal energy assistance program"
        if is_eligible
        else "Income exceeds 150% FPL"
    )
    return ProgramEligibility(
        program="CEAP",
        eligible=is_eligible,
        confidence=_confidence(annual, threshold),
        income_threshold=threshold,
        income_headroom=round(threshold - annual, 2),
        estimated_monthly_value=round(_benefit_value("CEAP", annual, profile), 2) if is_eligible else 0.0,
        reason=reason,
    )


PROGRAM_CHECKS = {
    "SNAP": _check_snap,
    "TANF": _check_tanf,
    "Medicaid": _check_medicaid,
    "CHIP": _check_chip,
    "Childcare_Subsidy": _check_childcare,
    "Section_8": _check_section_8,
    "CEAP": _check_ceap,
}
