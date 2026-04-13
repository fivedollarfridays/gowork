"""Stage builder -- constructs pathway stages from barrier sequence + wages.

Fuses the barrier sequencer (topological sort) with wage targets to
create ordered career stages. Each stage represents resolving barriers
needed to reach the next wage tier.
"""

from app.modules.plan.barrier_sequencer import (
    _WEEKS_PER_BARRIER,
    sequence_barriers,
)
from app.modules.pathway.types import PathwayStep

# Wage tier labels
_TIER_THRESHOLDS = [
    (10.0, "Entry-level position"),
    (13.0, "Stable employment"),
    (16.0, "Mid-range position"),
    (19.0, "Skilled position"),
    (22.0, "Career-track position"),
    (float("inf"), "Advanced career position"),
]


def wage_tier_label(wage: float) -> str:
    """Return a human-readable label for a wage tier."""
    for threshold, label in _TIER_THRESHOLDS:
        if wage <= threshold:
            return label
    return "Advanced career position"


def _assign_barriers_to_stages(
    barrier_ids: list[str],
    num_stages: int,
) -> list[list[str]]:
    """Distribute barriers across stages using topological order.

    Barriers that come first in the sequence go in earlier stages.
    """
    if not barrier_ids or num_stages == 0:
        return [[] for _ in range(max(num_stages, 1))]

    sequence = sequence_barriers(barrier_ids)
    ordered = [s.barrier_id for s in sequence.steps]

    # Distribute evenly across stages, front-loading
    assignments: list[list[str]] = [[] for _ in range(num_stages)]
    for i, bid in enumerate(ordered):
        stage_idx = min(i, num_stages - 1)
        assignments[stage_idx].append(bid)

    return assignments


def _compute_stage_weeks(barriers: list[str]) -> int:
    """Total weeks to resolve barriers in a stage."""
    return sum(_WEEKS_PER_BARRIER.get(b, 4) for b in barriers)


def build_stages(
    barrier_ids: list[str],
    wage_targets: list[float],
    jobs_per_wage: dict[float, int],
) -> list[PathwayStep]:
    """Build pathway stages by fusing barriers with wage progression.

    Each wage target becomes a stage. Barriers are distributed across
    stages in topological order (root causes first).

    Args:
        barrier_ids: Active barrier IDs to resolve across the pathway.
        wage_targets: Safe wage targets (ascending order).
        jobs_per_wage: Map of wage -> accessible job count.

    Returns:
        Ordered list of PathwayStep, one per wage target.
    """
    if not wage_targets:
        return []

    num_stages = len(wage_targets)
    barrier_assignments = _assign_barriers_to_stages(
        barrier_ids, num_stages,
    )

    steps: list[PathwayStep] = []
    cumulative_weeks = 0

    for i, wage in enumerate(wage_targets):
        stage_barriers = barrier_assignments[i] if i < len(barrier_assignments) else []
        stage_weeks = _compute_stage_weeks(stage_barriers)
        cumulative_weeks += stage_weeks

        steps.append(PathwayStep(
            stage=i + 1,
            title=wage_tier_label(wage),
            target_wage=wage,
            barriers_to_resolve=stage_barriers,
            estimated_weeks=cumulative_weeks,
            jobs_accessible=jobs_per_wage.get(wage, 0),
        ))

    return steps
