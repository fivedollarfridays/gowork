"""Static barrier priority map for MontgoWork.

Barriers with lower numbers surface first in the plan.
Childcare and transportation are immediate, concrete blockers.
Credit and training have longer timelines and can run in parallel.
"""

BARRIER_PRIORITY: dict[str, int] = {
    "childcare": 1,
    "transportation": 2,
    "housing": 3,
    "health": 4,
    "credit": 5,
    "criminal_record": 6,
    "training": 7,
}


def prioritize_barriers(user_barriers: list[str]) -> list[str]:
    """Sort barriers by priority (lowest number first). Unknown barriers last."""
    known = sorted(
        [b for b in user_barriers if b in BARRIER_PRIORITY],
        key=lambda b: BARRIER_PRIORITY[b],
    )
    unknown = [b for b in user_barriers if b not in BARRIER_PRIORITY]
    return known + unknown
