"""Resource eligibility engine — matches user profile to resource criteria.

City-aware: AL-only and TX-only rules live in ``app/cities/*/eligibility.py``
and are merged into the active rule set per request based on
``get_city_config().state``. The shape of the dict that consumers see is
unchanged; only the runtime *active* set is filtered to prevent AL rules
from matching FW resources (defense-in-depth on top of the city-tagged
resource pipeline).

The exported ``ELIGIBILITY_RULES`` is the UNION of universal + AL + TX
rules so existing tests (which iterate the dict to confirm every name is
recognized somewhere) keep working without churn.
"""

from enum import Enum
from typing import Optional

from app.cities.config import get_city_config
from app.cities.fort_worth.eligibility import FORT_WORTH_ELIGIBILITY_RULES
from app.cities.montgomery.eligibility import MONTGOMERY_ELIGIBILITY_RULES
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


# Universal eligibility rules — apply regardless of city.state.
# type: "open" → always likely
# type: "income" → income threshold check
# type: "enrollment" → requires specific program enrollment
# type: "compound" → multiple criteria
_UNIVERSAL_RULES: dict[str, dict] = {
    "GreenPath Financial": {"type": "open"},
    "Consumer Credit Counseling": {"type": "open"},
    "Salvation Army": {"type": "open"},
    "211 Helpline": {"type": "open"},
    "Family Guidance Center": {"type": "open"},
    # Federal programs (eligibility identical across states)
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
}


# Public union — kept for backward compatibility with tests that iterate
# the full rule set. At RUNTIME, ``_match_rule`` filters down to the
# active city's rules so AL resources can never match in a FW request.
ELIGIBILITY_RULES: dict[str, dict] = {
    **_UNIVERSAL_RULES,
    **MONTGOMERY_ELIGIBILITY_RULES,
    **FORT_WORTH_ELIGIBILITY_RULES,
}


def _active_rules_lower() -> dict[str, dict]:
    """Return lowercase-keyed rules for the city of the current request.

    Reads ``get_city_config().state`` (which honors the per-request
    ContextVar set in ``app.routes.assessment``) and merges the
    universal rules with the matching state's rules. AL rules are
    UNREACHABLE in a TX request and vice versa.
    """
    rules: dict[str, dict] = dict(_UNIVERSAL_RULES)
    state = (get_city_config().state or "").upper()
    if state == "AL":
        rules.update(MONTGOMERY_ELIGIBILITY_RULES)
    elif state == "TX":
        rules.update(FORT_WORTH_ELIGIBILITY_RULES)
    # Future cities: add their state branch here.
    return {key.lower(): rule for key, rule in rules.items()}


def _match_rule(resource_name: str) -> Optional[dict]:
    """Find the first matching rule by substring, scoped to the active city."""
    name_lower = resource_name.lower()
    for key, rule in _active_rules_lower().items():
        if key in name_lower:
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
