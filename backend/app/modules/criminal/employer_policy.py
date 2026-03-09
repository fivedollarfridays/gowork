"""Employer fair-chance policy models and eligibility logic.

Stores employer background-check policies and determines which employers
a person with a given RecordProfile is eligible to apply to.
"""

from pydantic import BaseModel, Field

from app.modules.criminal.record_profile import ChargeCategory, RecordProfile, RecordType


class EmployerPolicy(BaseModel):
    """An employer's criminal record screening policy."""

    employer_name: str
    fair_chance: bool = False
    excluded_charges: list[str] = Field(default_factory=list)
    lookback_years: int | None = None
    background_check_timing: str = "pre_offer"
    industry: str | None = None
    source: str | None = None
    montgomery_area: bool = True


def matches_record(policy: EmployerPolicy, profile: RecordProfile) -> bool:
    """Return True if a person with *profile* is eligible for *policy*.

    Rules:
    - Expunged records always match (sealed — employer cannot see them).
    - Empty profile (no charges/types) always matches.
    - Excluded charges: if any user charge overlaps excluded list → reject.
    - Lookback window: if conviction is within lookback_years → reject.
    - If years_since_conviction is None, lookback does not block.
    """
    # Expunged records are sealed — always eligible
    if profile.record_types == [RecordType.EXPUNGED]:
        return True

    # Empty profile — no record to screen against
    if not profile.charge_categories and not profile.record_types:
        return True

    # Excluded charges check
    user_charges = {c.value for c in profile.charge_categories}
    excluded = set(policy.excluded_charges)
    if user_charges & excluded:
        return False

    # Lookback window check
    if (
        policy.lookback_years is not None
        and profile.years_since_conviction is not None
        and profile.years_since_conviction < policy.lookback_years
    ):
        return False

    return True


def query_eligible_employers(
    policies: list[EmployerPolicy],
    profile: RecordProfile,
) -> list[EmployerPolicy]:
    """Filter and sort employers by eligibility for *profile*.

    Returns eligible employers with fair-chance employers sorted first.
    """
    eligible = [p for p in policies if matches_record(p, profile)]
    eligible.sort(key=lambda p: (not p.fair_chance, p.employer_name))
    return eligible
