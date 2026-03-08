"""Time-fit scorer: schedule conflict detection + barrier time cost analysis."""

from app.modules.matching.types import AvailableHours, BarrierType

BARRIER_TIME_COSTS: dict[BarrierType, float] = {
    BarrierType.CHILDCARE: 0.4,
    BarrierType.TRAINING: 0.25,
    BarrierType.HEALTH: 0.2,
    BarrierType.CREDIT: 0.15,
    BarrierType.TRANSPORTATION: 0.1,
    BarrierType.HOUSING: 0.1,
    BarrierType.CRIMINAL_RECORD: 0.05,
}

_SCHEDULE_WEIGHT = 0.6
_BARRIER_WEIGHT = 0.4
_MAX_BARRIER_PENALTY = 0.6


def _score_schedule(job: dict, schedule_type: AvailableHours) -> float:
    """1.0 if no schedule conflict, 0.2 if conflict detected.

    Uses pre-computed schedule_conflict flag from job_matcher._filter_by_schedule.
    """
    if schedule_type == AvailableHours.FLEXIBLE:
        return 1.0
    return 0.2 if job.get("schedule_conflict") else 1.0


def _score_barrier_time(barriers: list[BarrierType]) -> float:
    """1.0 - sum(costs), capped at 0.6 max penalty -> floor 0.4."""
    total_cost = sum(BARRIER_TIME_COSTS.get(b, 0.0) for b in barriers)
    capped_cost = min(total_cost, _MAX_BARRIER_PENALTY)
    return 1.0 - capped_cost


def score_time_fit(
    job: dict,
    schedule_type: AvailableHours,
    barriers: list[BarrierType],
) -> float:
    """Combined: schedule_score * 0.6 + barrier_time_score * 0.4."""
    schedule = _score_schedule(job, schedule_type)
    barrier = _score_barrier_time(barriers)
    return round(schedule * _SCHEDULE_WEIGHT + barrier * _BARRIER_WEIGHT, 2)
