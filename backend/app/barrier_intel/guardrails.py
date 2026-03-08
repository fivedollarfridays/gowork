"""Topic filter guardrails for barrier intelligence chat."""

import re

_DISALLOWED = re.compile(
    r"\b(?:legal\s+advice|attorney|lawyer|sue|lawsuit|immigration\s+status|"
    r"visa|deportation|medication|prescri(?:be|ption)|diagnos(?:e|is)|"
    r"medical\s+advice|invest(?:ment|ing)\s+advice|stock\s+tip|"
    r"guarantee(?:d)?\s+(?:income|return))\b",
    re.IGNORECASE,
)

SAFE_FALLBACK = (
    "I'm not able to help with that topic. For legal, medical, or immigration "
    "questions, please consult a qualified professional. "
    "I can help you with employment barriers, resources, and next steps."
)


def is_disallowed_topic(text: str) -> bool:
    """Return True if the text contains disallowed topic patterns."""
    return bool(_DISALLOWED.search(text))
