"""Outcome intelligence engine — closes the N+1 feedback loop.

Reads barrier resolution feedback and computes calibrated per-barrier
statistics: actual average weeks to resolve, success rates, and
confidence levels based on sample size.

These calibrated values feed back into the barrier_sequencer and
pathway engine to replace hardcoded estimates with real community data.

Zero LLM calls. Fully deterministic.
"""

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
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    sample_size: int = 0
    confidence: ConfidenceLevel = ConfidenceLevel.NONE


class CalibratedWeeks(BaseModel):
    """Calibrated barrier intelligence from community outcome data."""

    barriers: list[CalibratedBarrier] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.NONE

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
    weeks_to_resolve (int | None).

    Args:
        rows: Flat list of per-barrier feedback observations.

    Returns:
        CalibratedWeeks with per-barrier stats and overall confidence.
    """
    if not rows:
        return CalibratedWeeks(confidence=ConfidenceLevel.NONE)

    # Accumulate per-barrier stats
    totals: dict[str, int] = defaultdict(int)
    resolved_counts: dict[str, int] = defaultdict(int)
    weeks_sums: dict[str, float] = defaultdict(float)
    weeks_counts: dict[str, int] = defaultdict(int)

    for row in rows:
        bid = row.get("barrier_id")
        if not bid:
            continue
        totals[bid] += 1
        if row.get("resolved"):
            resolved_counts[bid] += 1
            weeks = row.get("weeks_to_resolve")
            if weeks is not None:
                weeks_sums[bid] += weeks
                weeks_counts[bid] += 1

    # Build calibrated barriers
    barriers: list[CalibratedBarrier] = []
    for bid, total in sorted(totals.items()):
        resolved = resolved_counts[bid]
        wc = weeks_counts[bid]
        avg_w = round(weeks_sums[bid] / wc, 1) if wc > 0 else 0.0
        rate = round(resolved / total, 4) if total > 0 else 0.0
        conf = _classify_confidence(total)
        barriers.append(CalibratedBarrier(
            barrier_id=bid,
            avg_weeks=avg_w,
            success_rate=rate,
            sample_size=total,
            confidence=conf,
        ))

    # Overall confidence: minimum across barriers, or based on total samples
    total_samples = sum(totals.values())
    overall = _classify_confidence(total_samples)

    return CalibratedWeeks(barriers=barriers, confidence=overall)
