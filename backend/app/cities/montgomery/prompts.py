"""Montgomery (AL) prompt fragments — referenced ONLY when city.state == 'AL'.

Centralizing these strings here prevents Montgomery context from leaking
into Fort Worth (TX) prompts.  Callers MUST gate on ``city.state == "AL"``
before reading from this module.
"""

# Used by: ai/client.py (_fallback_next_step) AL fallback narrative.
MONTGOMERY_FALLBACK_NEXT_STEP_PREFIX = (
    "Monday morning, head to the Alabama Career Center on Carter Hill Road. "
)

# Used by: ai/client.py (_build_fallback_actions) AL default action list.
MONTGOMERY_FALLBACK_ACTION = (
    "Visit the Alabama Career Center on Carter Hill Road in Montgomery "
    "for personalized guidance"
)

# Used by: barrier_intel/prompts.py system prompt for the AL career counselor.
MONTGOMERY_CAREER_CENTER_NAME = "the Montgomery Career Center"

# Used by: barrier_intel/guardrails.py hallucination disclaimer (AL).
MONTGOMERY_CAREER_CENTER_WITH_PHONE = "the Alabama Career Center at (334) 286-1746"

# Used by: ai/providers.py MockProvider (AL legacy branch).
MONTGOMERY_MOCK_CENTER = "the Alabama Career Center on Carter Hill Road"
