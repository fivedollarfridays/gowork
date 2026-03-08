"""Topic filter and hallucination guardrails for barrier intelligence chat."""

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

HALLUCINATION_DISCLAIMER = (
    "\n\n---\n*Some resources mentioned above could not be verified against our "
    "database. Please confirm details by contacting the Alabama Career Center "
    "at (334) 286-1746 before visiting.*"
)

# Matches capitalized multi-word proper nouns (2+ words, each capitalized)
_ORG_PATTERN = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")

# Common false positives: street/geographic suffixes, generic phrases
_FALSE_POSITIVE_SUFFIXES = {
    "road", "street", "avenue", "drive", "boulevard", "lane", "way",
    "route", "county", "city", "state",
}
_FALSE_POSITIVE_WORDS = {
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
}


def is_disallowed_topic(text: str) -> bool:
    """Return True if the text contains disallowed topic patterns."""
    return bool(_DISALLOWED.search(text))


def check_hallucinations(
    response: str,
    known_resource_names: list[str],
) -> str | None:
    """Check LLM response for resource names not in the known list.

    Returns a disclaimer string if hallucinated resources detected, else None.
    Does NOT block the response — caller appends disclaimer if returned.
    """
    if not response.strip() or not known_resource_names:
        return None

    mentioned = set(_ORG_PATTERN.findall(response))
    if not mentioned:
        return None

    known_lower = {name.lower() for name in known_resource_names}
    hallucinated = []
    for name in mentioned:
        name_lower = name.lower()
        words = name_lower.split()
        # Skip if last word is a common false positive (street name, etc.)
        if words[-1] in _FALSE_POSITIVE_SUFFIXES:
            continue
        # Skip if any word is a day/month name
        if any(w in _FALSE_POSITIVE_WORDS for w in words):
            continue
        # Check if any known resource contains this mention (or vice versa)
        if not any(
            name_lower in known or known in name_lower
            for known in known_lower
        ):
            hallucinated.append(name)

    if not hallucinated:
        return None

    names_str = ", ".join(hallucinated[:3])
    return f"Unverified: {names_str}{HALLUCINATION_DISCLAIMER}"
