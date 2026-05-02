"""Match Confidence Gate — Pattern 15 (graceful degradation).

When the system has no high-confidence match, it should ADMIT THAT
instead of pushing a weak top match.  This module classifies the plan's
ranked matches into confidence tiers and returns an honest verdict
the UI can surface.

Tiers (based on top match relevance_score):
- ``high``        : top >= 0.65            -> "we found a strong match"
- ``moderate``    : 0.50 <= top < 0.65     -> "promising but verify"
- ``maybe``       : 0.30 <= top < 0.50     -> "maybe match, visit WSTC"
- ``no_match``    : top < 0.30 or no jobs  -> "we don't have a fit yet"

The verdict carries a recommended ACTION — never "apply now" when the
top score is below 0.50.
"""

from __future__ import annotations

from dataclasses import dataclass

# Confidence score thresholds.  Tuned conservatively: 0.65 is the
# point at which the persona regression suite reliably surfaces top-3
# right-industry; below that we shouldn't over-promise.
HIGH_THRESHOLD = 0.65
MODERATE_THRESHOLD = 0.50
MAYBE_THRESHOLD = 0.30


@dataclass(frozen=True)
class ConfidenceVerdict:
    """Honest assessment of plan match strength.

    ``tier`` is one of: high, moderate, maybe, no_match.
    ``message`` is the resident-facing sentence the UI should show.
    ``recommended_action`` is the single concrete next step.
    """

    tier: str
    top_score: float
    message: str
    recommended_action: str
    match_count: int


_HIGH_MSG = "We found a strong match for you."
_MODERATE_MSG = (
    "We have a promising match. Verify the fit before applying — the "
    "fundamentals line up but a couple of factors are below ideal."
)
_MAYBE_MSG = (
    "We have a maybe match. The better path right now is to visit "
    "Workforce Solutions for Tarrant County for direct introductions to "
    "employers — they can pair you with roles that aren't in our index yet."
)
_NO_MATCH_MSG = (
    "We don't have a strong match for you in our current job index. This "
    "is honest information, not a dead end. Workforce Solutions for "
    "Tarrant County sees Fort Worth residents in your situation every "
    "day and has employer relationships our database doesn't reach."
)

_WSTC_ACTION = (
    "Visit Workforce Solutions for Tarrant County at 1200 Circle Dr, "
    "Fort Worth — they offer same-week direct intros to employers."
)
_APPLY_ACTION = "Apply directly through the listing this week."
_VERIFY_ACTION = "Apply this week, but also schedule a WSTC consult to verify fit."


def classify_confidence(matches: list) -> ConfidenceVerdict:
    """Return an honest confidence verdict for the ranked match list.

    ``matches`` is a list of objects (or dicts) with a ``relevance_score``
    field.  The function tolerates either Pydantic models or plain dicts.
    """
    count = len(matches) if matches else 0
    top_score = _extract_top_score(matches)

    if count == 0 or top_score < MAYBE_THRESHOLD:
        return ConfidenceVerdict(
            tier="no_match", top_score=top_score, message=_NO_MATCH_MSG,
            recommended_action=_WSTC_ACTION, match_count=count,
        )
    if top_score < MODERATE_THRESHOLD:
        return ConfidenceVerdict(
            tier="maybe", top_score=top_score, message=_MAYBE_MSG,
            recommended_action=_WSTC_ACTION, match_count=count,
        )
    if top_score < HIGH_THRESHOLD:
        return ConfidenceVerdict(
            tier="moderate", top_score=top_score, message=_MODERATE_MSG,
            recommended_action=_VERIFY_ACTION, match_count=count,
        )
    return ConfidenceVerdict(
        tier="high", top_score=top_score, message=_HIGH_MSG,
        recommended_action=_APPLY_ACTION, match_count=count,
    )


def _extract_top_score(matches: list) -> float:
    """Get the top relevance_score regardless of dict-vs-model shape."""
    if not matches:
        return 0.0
    top = matches[0]
    if hasattr(top, "relevance_score"):
        return float(getattr(top, "relevance_score") or 0.0)
    if isinstance(top, dict):
        return float(top.get("relevance_score") or 0.0)
    return 0.0
