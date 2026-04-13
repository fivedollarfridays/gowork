"""Outcome intelligence engine — closes the N+1 feedback loop.

Reads barrier resolution feedback and computes calibrated per-barrier
statistics: actual average weeks to resolve, success rates, variance,
and confidence levels based on sample size.

These calibrated values feed back into the barrier_sequencer and
pathway engine to replace hardcoded estimates with real community data.

Zero LLM calls. Fully deterministic.
"""

import math
from collections import defaultdict
from enum import Enum

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    """Confidence in calibrated values based on sample size."""

    NONE = "none"  # 0 samples
    LOW = "low"  # 1-2 samples
    MEDIUM = "medium"  # 3-9 samples
    HIGH = "high"  # 10+ samples


class CalibratedBarrier(BaseModel):
    """Calibrated statistics for a single barrier type."""

    barrier_id: str
    avg_weeks: float = 0.0
    stddev_weeks: float = 0.0
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    sample_size: int = 0
    confidence: ConfidenceLevel = ConfidenceLevel.NONE


class CalibratedWeeks(BaseModel):
    """Calibrated barrier intelligence from community outcome data."""

    barriers: list[CalibratedBarrier] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.NONE
    total_feedback_count: int = 0
    avg_plan_accuracy: float = 0.0

    def to_weeks_dict(self) -> dict[str, int]:
        """Export as weeks dict for barrier_sequencer integration.

        Only includes barriers with MEDIUM+ confidence and non-zero avg_weeks.
        Values are rounded to nearest integer.
        """
        result: dict[str, int] = {}
        for b in self.barriers:
            if b.confidence in (ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH):
                if b.avg_weeks > 0:
                    result[b.barrier_id] = round(b.avg_weeks)
        return result


def _classify_confidence(sample_size: int) -> ConfidenceLevel:
    """Map sample size to confidence level."""
    if sample_size >= 10:
        return ConfidenceLevel.HIGH
    if sample_size >= 3:
        return ConfidenceLevel.MEDIUM
    if sample_size >= 1:
        return ConfidenceLevel.LOW
    return ConfidenceLevel.NONE


def compute_calibrated_barriers(
    rows: list[dict],
) -> CalibratedWeeks:
    """Compute calibrated barrier stats from raw feedback rows.

    Each row is a dict with keys: barrier_id, resolved (bool),
    weeks_to_resolve (int | None), plan_accuracy (int | None).

    Args:
        rows: Flat list of per-barrier feedback observations.

    Returns:
        CalibratedWeeks with per-barrier stats, plan accuracy, and confidence.
    """
    if not rows:
        return CalibratedWeeks(confidence=ConfidenceLevel.NONE)

    # Accumulate per-barrier stats
    totals: dict[str, int] = defaultdict(int)
    resolved_counts: dict[str, int] = defaultdict(int)
    weeks_values: dict[str, list[float]] = defaultdict(list)
    plan_accuracies: list[int] = []

    for row in rows:
        bid = row.get("barrier_id")
        if not bid:
            continue
        totals[bid] += 1
        pa = row.get("plan_accuracy")
        if pa is not None:
            plan_accuracies.append(pa)
        if row.get("resolved"):
            resolved_counts[bid] += 1
            weeks = row.get("weeks_to_resolve")
            if weeks is not None:
                weeks_values[bid].append(float(weeks))

    # Build calibrated barriers
    barriers: list[CalibratedBarrier] = []
    for bid, total in sorted(totals.items()):
        resolved = resolved_counts[bid]
        wvals = weeks_values[bid]
        avg_w = round(sum(wvals) / len(wvals), 1) if wvals else 0.0
        stddev = _compute_stddev(wvals)
        rate = round(resolved / total, 4) if total > 0 else 0.0
        conf = _classify_confidence(total)
        barriers.append(CalibratedBarrier(
            barrier_id=bid,
            avg_weeks=avg_w,
            stddev_weeks=stddev,
            success_rate=rate,
            sample_size=total,
            confidence=conf,
        ))

    total_samples = sum(totals.values())
    overall = _classify_confidence(total_samples)
    avg_pa = _compute_avg_plan_accuracy(plan_accuracies)

    return CalibratedWeeks(
        barriers=barriers,
        confidence=overall,
        total_feedback_count=total_samples,
        avg_plan_accuracy=avg_pa,
    )


def _compute_stddev(values: list[float]) -> float:
    """Population standard deviation, rounded to 1 decimal place.

    Returns 0.0 for empty lists or single-value lists.
    """
    if len(values) <= 1:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return round(math.sqrt(variance), 1)


def _compute_avg_plan_accuracy(ratings: list[int]) -> float:
    """Average plan accuracy from non-None ratings.

    Returns 0.0 if no ratings are available.
    """
    if not ratings:
        return 0.0
    return round(sum(ratings) / len(ratings), 1)
