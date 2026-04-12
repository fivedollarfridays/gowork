"""Texas record clearing — expunction (Art. 55) and nondisclosure (Gov Code Ch. 411).

Texas provides TWO mechanisms for clearing criminal records:
1. Expunction: complete removal of the record
2. Nondisclosure: sealing the record from public access

Sources:
- TX Code of Criminal Procedure Art. 55 (expunction)
- TX Government Code Chapter 411, Subchapter E-1 (nondisclosure)
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.modules.criminal.expungement import ExpungementEligibility, ExpungementResult
from app.modules.criminal.record_profile import (
    ChargeCategory,
    RecordProfile,
    RecordType,
)

# Texas wait periods for expunction
_EXPUNCTION_WAIT_CLASS_C = 180  # days
_EXPUNCTION_WAIT_MISD_YEARS = 1
_EXPUNCTION_WAIT_FELONY_YEARS = 3

# Texas wait periods for nondisclosure
_NONDISCLOSURE_WAIT_MISD_YEARS = 2
_NONDISCLOSURE_WAIT_FELONY_YEARS = 5

_FILING_FEE = "$280"

# Charges ineligible for nondisclosure
_NONDISCLOSURE_BARRED: set[ChargeCategory] = {
    ChargeCategory.SEX_OFFENSE,
}


class TexasRecordClearingResult(BaseModel):
    """Combined result for both Texas record clearing mechanisms."""

    expunction_eligible: bool = False
    expunction_result: ExpungementResult = Field(
        default_factory=lambda: ExpungementResult(
            eligibility=ExpungementEligibility.NOT_ELIGIBLE
        )
    )
    nondisclosure_eligible: bool = False
    nondisclosure_result: ExpungementResult = Field(
        default_factory=lambda: ExpungementResult(
            eligibility=ExpungementEligibility.NOT_ELIGIBLE
        )
    )


def _legal_aid_steps() -> list[str]:
    return [
        "Contact Legal Aid of NorthWest Texas (817-336-3943) for free consultation",
        "Gather court records from Tarrant County District Clerk",
    ]


def _expunction_steps() -> list[str]:
    return _legal_aid_steps() + [
        "File petition for expunction in district court ($280 filing fee)",
        "Attend hearing for expunction order",
    ]


def _nondisclosure_steps() -> list[str]:
    return _legal_aid_steps() + [
        "File petition for order of nondisclosure ($280 filing fee)",
        "Court reviews petition and issues order if eligible",
    ]


def _check_expunction(profile: RecordProfile) -> ExpungementResult:
    """Check Texas expunction eligibility (Art. 55)."""
    # Arrest-only: eligible immediately
    if all(rt == RecordType.ARREST_ONLY for rt in profile.record_types):
        return ExpungementResult(
            eligibility=ExpungementEligibility.ELIGIBLE_NOW,
            years_remaining=0,
            steps=_expunction_steps(),
            filing_fee=_FILING_FEE,
            notes="Arrest-only records are eligible for expunction in Texas.",
        )

    # Acquittal: eligible immediately
    if profile.was_acquitted:
        return ExpungementResult(
            eligibility=ExpungementEligibility.ELIGIBLE_NOW,
            years_remaining=0,
            steps=_expunction_steps(),
            filing_fee=_FILING_FEE,
            notes="Acquitted charges are eligible for immediate expunction.",
        )

    # Sex offenses: never expungeable via conviction path
    if ChargeCategory.SEX_OFFENSE in profile.charge_categories:
        return ExpungementResult(
            eligibility=ExpungementEligibility.NOT_ELIGIBLE,
            notes="This charge is not eligible for expunction under Texas law.",
        )

    # Convictions generally cannot be expunged in Texas
    # (expunction is primarily for non-convictions)
    return ExpungementResult(
        eligibility=ExpungementEligibility.NOT_ELIGIBLE,
        notes=(
            "Texas expunction is primarily for arrests without conviction, "
            "acquittals, and pardons. See nondisclosure for conviction sealing."
        ),
    )


def _is_nondisclosure_barred(profile: RecordProfile) -> bool:
    """Check if charges are categorically barred from nondisclosure."""
    for cat in profile.charge_categories:
        if cat in _NONDISCLOSURE_BARRED:
            return True
    # Family violence is separately barred
    if profile.is_family_violence:
        return True
    return False


def _nondisclosure_wait_result(
    wait_years: int, years_since: int | None,
) -> ExpungementResult:
    """Build the nondisclosure result based on wait period status."""
    if years_since is None:
        return ExpungementResult(
            eligibility=ExpungementEligibility.ELIGIBLE_FUTURE,
            steps=_nondisclosure_steps(),
            filing_fee=_FILING_FEE,
            notes=f"May be eligible after {wait_years} years from deferred adjudication completion.",
        )
    years_remaining = max(0, wait_years - years_since)
    if years_remaining == 0:
        return ExpungementResult(
            eligibility=ExpungementEligibility.ELIGIBLE_NOW,
            years_remaining=0,
            steps=_nondisclosure_steps(),
            filing_fee=_FILING_FEE,
            notes="You may be eligible to file for nondisclosure now.",
        )
    return ExpungementResult(
        eligibility=ExpungementEligibility.ELIGIBLE_FUTURE,
        years_remaining=years_remaining,
        steps=_nondisclosure_steps(),
        filing_fee=_FILING_FEE,
        notes=f"Eligible to file in approximately {years_remaining} year{'s' if years_remaining != 1 else ''}.",
    )


def _check_nondisclosure(profile: RecordProfile) -> ExpungementResult:
    """Check Texas nondisclosure eligibility (Gov Code Ch. 411 E-1)."""
    if not profile.completed_deferred_adjudication:
        return ExpungementResult(
            eligibility=ExpungementEligibility.NOT_ELIGIBLE,
            notes="Nondisclosure requires completed deferred adjudication.",
        )

    if _is_nondisclosure_barred(profile):
        return ExpungementResult(
            eligibility=ExpungementEligibility.NOT_ELIGIBLE,
            notes="This charge type is not eligible for nondisclosure in Texas.",
        )

    has_felony = RecordType.FELONY in profile.record_types
    wait_years = _NONDISCLOSURE_WAIT_FELONY_YEARS if has_felony else _NONDISCLOSURE_WAIT_MISD_YEARS
    return _nondisclosure_wait_result(wait_years, profile.years_since_conviction)


def check_texas_record_clearing(
    profile: RecordProfile | None,
) -> TexasRecordClearingResult:
    """Check both expunction and nondisclosure eligibility under Texas law."""
    if profile is None or not profile.record_types:
        return TexasRecordClearingResult()

    expunction = _check_expunction(profile)
    nondisclosure = _check_nondisclosure(profile)

    return TexasRecordClearingResult(
        expunction_eligible=expunction.eligibility == ExpungementEligibility.ELIGIBLE_NOW,
        expunction_result=expunction,
        nondisclosure_eligible=nondisclosure.eligibility == ExpungementEligibility.ELIGIBLE_NOW,
        nondisclosure_result=nondisclosure,
    )
