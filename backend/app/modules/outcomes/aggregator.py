"""Outcome aggregator -- computes community insights from outcome records.

This is the READ side of the N+1 intelligence loop. Takes raw outcome
records and produces aggregated barrier resolution statistics, plan
accuracy averages, and community intelligence.

Zero LLM calls. Fully deterministic.
"""

from collections import defaultdict

from app.modules.outcomes.tracker import OutcomeTracker
from app.modules.outcomes.types import BarrierInsight, CommunityInsights


def _aggregate_barrier_stats(
    outcomes: list,
) -> list[BarrierInsight]:
    """Compute per-barrier statistics from a list of outcome records."""
    totals: dict[str, int] = defaultdict(int)
    resolved_counts: dict[str, int] = defaultdict(int)
    weeks_sums: dict[str, float] = defaultdict(float)
    weeks_counts: dict[str, int] = defaultdict(int)

    for record in outcomes:
        for bo in record.barrier_outcomes:
            totals[bo.barrier_id] += 1
            if bo.resolved:
                resolved_counts[bo.barrier_id] += 1
                if bo.weeks_to_resolve is not None:
                    weeks_sums[bo.barrier_id] += bo.weeks_to_resolve
                    weeks_counts[bo.barrier_id] += 1

    insights: list[BarrierInsight] = []
    for barrier_id, total in totals.items():
        resolved = resolved_counts[barrier_id]
        wc = weeks_counts[barrier_id]
        avg_weeks = round(weeks_sums[barrier_id] / wc, 2) if wc > 0 else 0.0
        success_rate = round(resolved / total, 4) if total > 0 else 0.0
        insights.append(BarrierInsight(
            barrier_id=barrier_id,
            resolution_count=total,
            avg_weeks_to_resolve=avg_weeks,
            success_rate=success_rate,
        ))

    insights.sort(key=lambda b: b.resolution_count, reverse=True)
    return insights


def _compute_avg_plan_accuracy(outcomes: list) -> float:
    """Average plan accuracy from outcomes that include a rating."""
    ratings = [o.plan_accuracy for o in outcomes if o.plan_accuracy is not None]
    if not ratings:
        return 0.0
    return round(sum(ratings) / len(ratings), 4)


def compute_insights(tracker: OutcomeTracker, city: str) -> CommunityInsights:
    """Compute aggregate community insights for a city.

    Args:
        tracker: OutcomeTracker containing recorded outcomes.
        city: City slug to scope results (e.g. 'fort-worth').

    Returns:
        CommunityInsights with barrier stats and plan accuracy.
    """
    outcomes = tracker.get_outcomes_for_city(city)
    barrier_insights = _aggregate_barrier_stats(outcomes)
    avg_accuracy = _compute_avg_plan_accuracy(outcomes)

    return CommunityInsights(
        total_outcomes=len(outcomes),
        barrier_insights=barrier_insights,
        avg_plan_accuracy=avg_accuracy,
        city=city,
    )
