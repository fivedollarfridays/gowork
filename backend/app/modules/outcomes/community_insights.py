"""'People Like You' Community Insights engine.

Transforms calibrated barrier outcome data into personalized,
deterministic, city-aware community insight messages. No LLM calls.
No AI. Pure deterministic logic.

A Fort Worth resident sees: "15 people in Fort Worth with criminal
records cleared them in about 8 weeks (80% success rate)."

That's not a feature. That's someone feeling less alone.
"""

from typing import Literal

from pydantic import BaseModel, Field

from app.modules.outcomes.intelligence import (
    CalibratedBarrier,
    CalibratedWeeks,
    ConfidenceLevel,
)

MetricType = Literal["resolution_time", "success_rate", "recommendation"]

# Human-readable barrier labels
_BARRIER_LABELS: dict[str, str] = {
    "criminal_record": "criminal records",
    "credit": "credit issues",
    "transportation": "transportation barriers",
    "childcare": "childcare barriers",
    "housing": "housing instability",
    "health": "health barriers",
    "training": "training gaps",
}

# Minimum sample size thresholds
_SMALL_SAMPLE_THRESHOLD = 5


class CommunityInsight(BaseModel):
    """A single personalized community insight message."""

    message: str
    barrier_type: str
    confidence: str
    sample_size: int = 0
    metric_type: MetricType = "resolution_time"


def generate_insights(
    calibrated: CalibratedWeeks,
    user_barriers: list[str],
    city_name: str,
) -> list[CommunityInsight]:
    """Generate personalized community insight messages.

    Pure function: same input always produces same output.
    No LLM. No randomness. Deterministic string formatting from data.

    Args:
        calibrated: Calibrated barrier data from the intelligence engine.
        user_barriers: List of barrier IDs from the user's assessment.
        city_name: Display name of the user's city (e.g. "Fort Worth").

    Returns:
        List of CommunityInsight messages, ordered by confidence.
    """
    if not user_barriers:
        return []

    if not calibrated.barriers or calibrated.total_feedback_count == 0:
        return [generate_cold_start_insight(city_name, user_barriers)]

    # Build lookup for quick access
    barrier_lookup = {b.barrier_id: b for b in calibrated.barriers}

    insights: list[CommunityInsight] = []
    for bid in user_barriers:
        stats = barrier_lookup.get(bid)
        if stats is None or stats.confidence == ConfidenceLevel.NONE:
            continue
        insights.append(_format_resolution_insight(bid, stats, city_name))
        if stats.success_rate > 0:
            insights.append(_format_success_rate_insight(bid, stats, city_name))

    if not insights:
        return [generate_cold_start_insight(city_name, user_barriers)]

    # Add recommendation insight when multiple barriers have data
    matched = [
        (bid, barrier_lookup[bid])
        for bid in user_barriers
        if bid in barrier_lookup
        and barrier_lookup[bid].confidence != ConfidenceLevel.NONE
    ]
    if len(matched) >= 2:
        rec = _format_recommendation_insight(matched, city_name)
        if rec is not None:
            insights.append(rec)

    return insights


def generate_cold_start_insight(
    city_name: str,
    user_barriers: list[str] | None = None,
) -> CommunityInsight:
    """Generate an encouraging first-user message when no data exists.

    Honest about being early, but frames it positively: the user's
    experience will help improve recommendations for others.
    """
    message = (
        f"You're among the first in {city_name} to use this system. "
        f"Your experience will help improve guidance for future "
        f"{city_name} residents."
    )
    barrier_type = user_barriers[0] if user_barriers else "general"
    return CommunityInsight(
        message=message,
        barrier_type=barrier_type,
        confidence="none",
        sample_size=0,
        metric_type="recommendation",
    )


def _format_resolution_insight(
    barrier_id: str,
    stats: CalibratedBarrier,
    city_name: str,
) -> CommunityInsight:
    """Format a resolution time insight for a barrier.

    Uses confident language for HIGH confidence (exact count),
    cautious language for LOW/MEDIUM (vague count).
    """
    label = _BARRIER_LABELS.get(barrier_id, barrier_id.replace("_", " "))
    weeks = round(stats.avg_weeks)
    people_phrase = _format_people_phrase(stats.sample_size, city_name)

    message = (
        f"{people_phrase} with {label} resolved them "
        f"in about {weeks} weeks."
    )
    return CommunityInsight(
        message=message,
        barrier_type=barrier_id,
        confidence=stats.confidence.value,
        sample_size=stats.sample_size,
        metric_type="resolution_time",
    )


def _format_success_rate_insight(
    barrier_id: str,
    stats: CalibratedBarrier,
    city_name: str,
) -> CommunityInsight:
    """Format a success rate insight for a barrier."""
    label = _BARRIER_LABELS.get(barrier_id, barrier_id.replace("_", " "))
    rate_pct = round(stats.success_rate * 100)
    people_phrase = _format_people_phrase(stats.sample_size, city_name)

    message = (
        f"{people_phrase} with {label} had an "
        f"{rate_pct}% success rate."
    )
    return CommunityInsight(
        message=message,
        barrier_type=barrier_id,
        confidence=stats.confidence.value,
        sample_size=stats.sample_size,
        metric_type="success_rate",
    )


def _format_recommendation_insight(
    matched_barriers: list[tuple[str, CalibratedBarrier]],
    city_name: str,
) -> CommunityInsight | None:
    """Format a recommendation based on multi-barrier comparison.

    Suggests resolving the fastest/highest-success-rate barrier first.
    Only generated when 2+ barriers have data.
    """
    if len(matched_barriers) < 2:
        return None

    # Find the barrier with shortest avg_weeks (quickest win)
    fastest = min(matched_barriers, key=lambda x: x[1].avg_weeks if x[1].avg_weeks > 0 else float("inf"))
    fastest_id, fastest_stats = fastest
    fastest_label = _BARRIER_LABELS.get(fastest_id, fastest_id.replace("_", " "))
    weeks = round(fastest_stats.avg_weeks)

    message = (
        f"People in {city_name} who resolved {fastest_label} first "
        f"(about {weeks} weeks) found it easier to tackle "
        f"their remaining barriers."
    )
    return CommunityInsight(
        message=message,
        barrier_type=fastest_id,
        confidence=fastest_stats.confidence.value,
        sample_size=fastest_stats.sample_size,
        metric_type="recommendation",
    )


def _format_people_phrase(sample_size: int, city_name: str) -> str:
    """Format the people count phrase based on sample size.

    HIGH confidence (10+): "15 people in Fort Worth"
    MEDIUM (3-9): "Several people in Fort Worth"
    LOW (1-2): "A small number of people in Fort Worth"
    """
    if sample_size >= _SMALL_SAMPLE_THRESHOLD:
        return f"{sample_size} people in {city_name}"
    if sample_size >= 3:
        return f"Several people in {city_name}"
    return f"A small number of people in {city_name}"
