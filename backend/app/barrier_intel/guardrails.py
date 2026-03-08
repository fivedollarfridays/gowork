"""Topic filter and hallucination guardrails for barrier intelligence chat."""

import re

_DISALLOWED_PATTERNS: list[str] = [
    r"\b(sue|lawsuit|legal\s+action|attorney|lawyer|litigation)\b",
    r"\b(diagnosis|medication|prescri|medical\s+advice|doctor)\b",
    r"\b(immigration|visa|green\s+card|deportation|asylum|citizenship)\b",
    r"\b(guaranteed?\s+(income|job|return|benefit))\b",
    r"\b(tax\s+fraud|bankruptcy\s+filing)\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _DISALLOWED_PATTERNS]

SAFE_FALLBACK = (
    "I'm not able to help with that topic — it's outside my scope. "
    "For legal, medical, or immigration questions, please contact a qualified professional. "
    "I'm here to help you find employment resources and next steps in Montgomery."
)


def is_disallowed_topic(text: str) -> bool:
    """Return True if the text matches any disallowed pattern."""
    return any(p.search(text) for p in _COMPILED)


def check_hallucinations(
    response_text: str,
    top_resources: list[dict],
    retrieved_doc_titles: list[str],
) -> str:
    """Append disclaimer if response references resources not in context."""
    known_names = {r.get("name", "").lower() for r in top_resources}
    known_names.update(t.lower() for t in retrieved_doc_titles)

    resource_pattern = re.compile(r"[A-Z][a-zA-Z\s]{3,40}(?:Center|Program|Service|Office|Fund)")
    mentioned = resource_pattern.findall(response_text)
    unknown = [m for m in mentioned if m.lower() not in known_names]

    if unknown:
        return (
            response_text
            + "\n\n_Note: Some resources mentioned above may not be in our verified database. "
            "Please confirm availability with a career counselor._"
        )
    return response_text
