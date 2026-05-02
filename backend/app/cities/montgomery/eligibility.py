"""Montgomery (AL) resource eligibility rules — referenced ONLY when
city.state == 'AL'.

Centralizing these here matches the pattern in
``app/cities/montgomery/prompts.py`` (the AI-prompt agent purge): keep
city-specific literals in their own module so they can never leak into
the wrong city's request path.

Callers MUST gate on ``city.state == "AL"`` before merging this dict
into the active eligibility set.

Schema mirrors ``app.modules.resources.eligibility.ELIGIBILITY_RULES``
exactly:
    type: "open"        → always likely
    type: "income"      → income threshold check
    type: "enrollment"  → requires specific program enrollment
    type: "compound"    → multiple criteria (income + dependents)
"""


MONTGOMERY_ELIGIBILITY_RULES: dict[str, dict] = {
    # Career center / training
    "Montgomery Career Center": {"type": "open"},
    "Trenholm State": {"type": "open"},
    "AIDT": {"type": "open"},
    # Food / emergency
    "Montgomery Area Food Bank": {"type": "open"},
    # Universal referral (Alabama's "OneAlabama Community Resource Network")
    "OneAlabama": {"type": "open"},
    # Transit
    "MATS": {"type": "open"},
    # Returning citizens / re-entry
    "MPACT": {"type": "open"},
    "MRWTC": {"type": "open"},
    # Program enrollment required (Alabama JOBS Program — DHR's TANF
    # work-readiness arm)
    "JOBS Program": {
        "type": "enrollment",
        "requires_program": "TANF",
    },
}
