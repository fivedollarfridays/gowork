"""Dallas (TX) resource eligibility rules — referenced ONLY when
city.state == 'TX'.

Centralizing these here matches the pattern in
``app/cities/fort_worth/eligibility.py`` (the sister TX city): keep
city-specific literals in their own module so they can never leak into
the wrong city's request path.

Callers MUST gate on ``city.state == "TX"`` before merging this dict
into the active eligibility set.

Schema mirrors ``app.modules.resources.eligibility.ELIGIBILITY_RULES``
exactly:
    type: "open"        → always likely
    type: "income"      → income threshold check
    type: "enrollment"  → requires specific program enrollment
    type: "compound"    → multiple criteria (income + dependents)
"""

from app.modules.benefits.thresholds import CHILDCARE_SMI_LIMIT_PCT


DALLAS_ELIGIBILITY_RULES: dict[str, dict] = {
    # Universal job-seeker / training resources
    "Workforce Solutions Greater Dallas": {"type": "open"},
    "Dallas College": {"type": "open"},
    # Transit
    "DART": {"type": "open"},
    # Health (sliding-scale, no income gate at the entry door)
    "Parkland Health": {"type": "open"},
    # Legal aid (open intake) — same statewide provider as FW, Dallas branch
    "Legal Aid of NorthWest Texas — Dallas": {"type": "open"},
    # Housing (open intake; case-by-case program qualification downstream)
    "Dallas Housing Authority": {"type": "open"},
    # Childcare (Texas Rising Star is the public-quality rating; open lookup)
    "Texas Rising Star": {"type": "open"},
    # Childcare subsidy — TWC Child Care Services has the standard SMI gate
    "TWC Child Care Services": {
        "type": "compound",
        "income_check": "smi",
        "max_income_pct_smi": CHILDCARE_SMI_LIMIT_PCT,
        "requires_any_children": True,
    },
    # Universal referral hotline (the Dallas analog to AL's OneAlabama)
    "North Texas 211": {"type": "open"},
}
