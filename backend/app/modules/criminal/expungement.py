"""Alabama expungement eligibility check — Act 2021-507.

Determines whether a criminal record may qualify for expungement under
Alabama law, with estimated timeline and actionable next steps.
"""

from enum import Enum

from pydantic import BaseModel, Field

from app.modules.criminal.record_profile import (
    ChargeCategory,
    RecordProfile,
    RecordType,
)

# Alabama Act 2021-507 thresholds
_MISDEMEANOR_WAIT_YEARS = 3
_FELONY_WAIT_YEARS = 5
_FILING_FEE = "$300"

# Charges that can never be expunged
_NEVER_EXPUNGEABLE: set[ChargeCategory] = {ChargeCategory.SEX_OFFENSE}
_VIOLENT_CATEGORY: ChargeCategory = ChargeCategory.VIOLENCE


class ExpungementEligibility(str, Enum):
    ELIGIBLE_NOW = "eligible_now"
    ELIGIBLE_FUTURE = "eligible_future"
    NOT_ELIGIBLE = "not_eligible"
    UNKNOWN = "unknown"


class ExpungementResult(BaseModel):
    """Result of Alabama expungement eligibility check."""

    eligibility: ExpungementEligibility
    years_remaining: int | None = None
    steps: list[str] = Field(default_factory=list)
    filing_fee: str | None = None
    notes: str | None = None


def _is_never_expungeable(profile: RecordProfile) -> bool:
    """Check if any charges are categorically ineligible."""
    for cat in profile.charge_categories:
        if cat in _NEVER_EXPUNGEABLE:
            return True
    return (
        _VIOLENT_CATEGORY in profile.charge_categories
        and RecordType.FELONY in profile.record_types
    )


def _eligible_steps() -> list[str]:
    return [
        "Contact Legal Services Alabama (1-866-456-4995) for free consultation",
        "Gather court records from the county of conviction",
        "File petition for expungement in circuit court ($300 fee, waivable)",
        "Attend hearing — judge reviews eligibility under Act 2021-507",
    ]


def _future_steps(years_remaining: int | None) -> list[str]:
    steps = list(_eligible_steps())
    if years_remaining and years_remaining > 0:
        steps.insert(0, f"Wait {years_remaining} more year{'s' if years_remaining != 1 else ''} from sentence completion")
    else:
        steps.insert(0, "Complete your sentence and all court-ordered obligations")
    return steps


def _check_early_returns(profile: RecordProfile) -> ExpungementResult | None:
    """Handle immediate-return cases: expunged, arrest-only, never-expungeable."""
    if profile.record_types and all(rt == RecordType.EXPUNGED for rt in profile.record_types):
        return ExpungementResult(
            eligibility=ExpungementEligibility.ELIGIBLE_NOW,
            years_remaining=0,
            notes="Your record is already expunged.",
        )
    if all(rt == RecordType.ARREST_ONLY for rt in profile.record_types):
        return ExpungementResult(
            eligibility=ExpungementEligibility.ELIGIBLE_NOW,
            years_remaining=0,
            steps=_eligible_steps(),
            filing_fee=_FILING_FEE,
            notes="Arrest-only records are eligible for immediate expungement.",
        )
    if _is_never_expungeable(profile):
        return ExpungementResult(
            eligibility=ExpungementEligibility.NOT_ELIGIBLE,
            notes="This charge type is not eligible for expungement under Alabama law.",
        )
    return None


def _check_wait_period(profile: RecordProfile, wait_years: int) -> ExpungementResult:
    """Evaluate wait period and sentence completion."""
    if profile.years_since_conviction is None:
        return ExpungementResult(
            eligibility=ExpungementEligibility.ELIGIBLE_FUTURE,
            steps=_future_steps(None),
            filing_fee=_FILING_FEE,
            notes=f"May be eligible after {wait_years} years from sentence completion.",
        )
    years_remaining = max(0, wait_years - profile.years_since_conviction)
    if not profile.completed_sentence:
        return ExpungementResult(
            eligibility=ExpungementEligibility.ELIGIBLE_FUTURE,
            years_remaining=years_remaining if years_remaining > 0 else None,
            steps=_future_steps(years_remaining if years_remaining > 0 else None),
            filing_fee=_FILING_FEE,
            notes="Complete your sentence before filing for expungement.",
        )
    if years_remaining == 0:
        return ExpungementResult(
            eligibility=ExpungementEligibility.ELIGIBLE_NOW,
            years_remaining=0,
            steps=_eligible_steps(),
            filing_fee=_FILING_FEE,
            notes="You may be eligible to file for expungement now.",
        )
    return ExpungementResult(
        eligibility=ExpungementEligibility.ELIGIBLE_FUTURE,
        years_remaining=years_remaining,
        steps=_future_steps(years_remaining),
        filing_fee=_FILING_FEE,
        notes=f"Eligible to file in approximately {years_remaining} year{'s' if years_remaining != 1 else ''}.",
    )


def check_expungement_eligibility(
    profile: RecordProfile | None,
) -> ExpungementResult:
    """Check expungement eligibility under Alabama Act 2021-507."""
    if profile is None or not profile.record_types:
        return ExpungementResult(
            eligibility=ExpungementEligibility.UNKNOWN,
            notes="Provide your record details for an eligibility estimate.",
        )
    early = _check_early_returns(profile)
    if early is not None:
        return early
    has_felony = RecordType.FELONY in profile.record_types
    wait_years = _FELONY_WAIT_YEARS if has_felony else _MISDEMEANOR_WAIT_YEARS
    return _check_wait_period(profile, wait_years)
