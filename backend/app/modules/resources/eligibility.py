"""Resource eligibility engine — matches user profile to resource criteria."""

from enum import Enum
from typing import Optional

from app.modules.benefits.thresholds import (
    CHILDCARE_SMI_LIMIT_PCT,
    FPL_2026,
    SMI_2026,
)
from app.modules.benefits.types import BenefitsProfile
from app.modules.matching.types import Resource


class EligibilityStatus(str, Enum):
    """User's eligibility for a resource."""

    LIKELY = "likely"
    CHECK = "check"
    UNKNOWN = "unknown"


# Eligibility rules keyed by resource name (substring match).
# type: "open" → always likely
# type: "income" → income threshold check
# type: "enrollment" → requires specific program enrollment
# type: "compound" → multiple criteria
ELIGIBILITY_RULES: dict[str, dict] = {
    # Open to all
    "Montgomery Career Center": {"type": "open"},
    "GreenPath Financial": {"type": "open"},
    "Consumer Credit Counseling": {"type": "open"},
    "Trenholm State": {"type": "open"},
    "Montgomery Area Food Bank": {"type": "open"},
    "Salvation Army": {"type": "open"},
    "211 Helpline": {"type": "open"},
    "OneAlabama": {"type": "open"},
    "MATS": {"type": "open"},
    "AIDT": {"type": "open"},
    # Returning citizens
    "MPACT": {"type": "open"},
    "MRWTC": {"type": "open"},
    # Program enrollment required
    "JOBS Program": {
        "type": "enrollment",
        "requires_program": "TANF",
    },
    # Income + dependents
    "Head Start": {
        "type": "compound",
        "max_income_pct_fpl": 1.0,
        "requires_young_children": True,
    },
    "Child Care Subsidy": {
        "type": "compound",
        "income_check": "smi",
        "max_income_pct_smi": CHILDCARE_SMI_LIMIT_PCT,
        "requires_any_children": True,
    },
    "Family Guidance Center": {"type": "open"},
}


def _match_rule(resource_name: str) -> Optional[dict]:
    """Find the first matching rule by substring."""
    for key, rule in ELIGIBILITY_RULES.items():
        if key.lower() in resource_name.lower():
            return rule
    return None


def _annual_income(profile: BenefitsProfile) -> float:
    return profile.current_monthly_income * 12


def check_eligibility(
    resource: Resource,
    profile: Optional[BenefitsProfile],
) -> EligibilityStatus:
    """Determine user eligibility for a resource.

    Returns LIKELY if user clearly qualifies, CHECK if uncertain,
    UNKNOWN if no profile or no rule exists.
    """
    if profile is None:
        return EligibilityStatus.UNKNOWN

    rule = _match_rule(resource.name)
    if rule is None:
        return EligibilityStatus.UNKNOWN

    rule_type = rule["type"]

    if rule_type == "open":
        return EligibilityStatus.LIKELY

    if rule_type == "enrollment":
        program = rule["requires_program"]
        if program in profile.enrolled_programs:
            return EligibilityStatus.LIKELY
        return EligibilityStatus.CHECK

    if rule_type == "compound":
        return _check_compound(rule, profile)

    return EligibilityStatus.UNKNOWN


def _check_compound(rule: dict, profile: BenefitsProfile) -> EligibilityStatus:
    """Evaluate compound eligibility (income + dependents)."""
    annual = _annual_income(profile)
    hs = profile.household_size

    # Check children requirement first
    if rule.get("requires_young_children"):
        if profile.dependents_under_6 < 1:
            return EligibilityStatus.CHECK

    if rule.get("requires_any_children"):
        total_kids = profile.dependents_under_6 + profile.dependents_6_to_17
        if total_kids < 1:
            return EligibilityStatus.CHECK

    # Income check
    if "max_income_pct_fpl" in rule:
        fpl = FPL_2026.get(hs, FPL_2026[4])
        threshold = fpl * rule["max_income_pct_fpl"]
        if annual <= threshold:
            return EligibilityStatus.LIKELY
        return EligibilityStatus.CHECK

    if rule.get("income_check") == "smi":
        smi = SMI_2026.get(hs, SMI_2026[4])
        threshold = smi * rule["max_income_pct_smi"]
        if annual <= threshold:
            return EligibilityStatus.LIKELY
        return EligibilityStatus.CHECK

    return EligibilityStatus.LIKELY
