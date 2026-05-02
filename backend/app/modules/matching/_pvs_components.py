"""Tiny helpers extracted from ``pvs_scorer`` to keep the parent file
under the architecture line / function limits.

Each helper is one-screen pure logic — no I/O, no side effects.
Lives next to ``pvs_scorer`` and is imported back via leading-underscore
names so the public API of the matching package is unchanged.
"""

from __future__ import annotations

from typing import Optional

from app.modules.benefits.types import BenefitsProfile
from app.modules.matching.distance import compute_job_distance, distance_score
from app.modules.matching.salary_parser import (
    SalaryInfo,
    score_earnings,
)


def select_income_score(
    salary: Optional[SalaryInfo],
    bp: Optional[BenefitsProfile],
    net_score_fn,
) -> float:
    """Choose net-income vs gross-earnings scoring path.

    ``net_score_fn`` is injected so this module doesn't import the
    private ``_score_net_income`` from pvs_scorer (would re-create
    a cycle). Caller passes the helper.
    """
    if salary and bp and bp.enrolled_programs:
        return net_score_fn(salary, bp)
    return score_earnings(salary)


def weighted_sum_pvs(
    income: float, proximity: float, time_fit: float, barrier_compat: float,
    resume: float, has_resume: bool,
    weights_no_resume: tuple[float, float, float, float],
    weights_with_resume: tuple[float, float, float, float, float],
) -> float:
    """Combine the four (or five) PVS components.

    Splits cleanly so the parent ``compute_pvs`` stays under the
    arch limit. Weight tables are passed in to keep this module
    constants-free.
    """
    if has_resume:
        wn, wp, wt, wb, wr = weights_with_resume
        return (
            wn * income + wp * proximity + wt * time_fit
            + wb * barrier_compat + wr * resume
        )
    wn, wp, wt, wb = weights_no_resume
    return wn * income + wp * proximity + wt * time_fit + wb * barrier_compat


def distance_boost_value(
    user_zip: str,
    job_lat: Optional[float],
    job_lng: Optional[float],
    transit_dependent: bool,
    weight: float,
) -> float:
    """Distance-from-ZIP additive boost; 0 when any signal is missing.

    Always 0 for users with a vehicle, for unknown ZIPs, or for
    un-geocoded jobs — never invents a coordinate.
    """
    if not transit_dependent:
        return 0.0
    miles = compute_job_distance(user_zip, job_lat, job_lng)
    if miles is None:
        return 0.0
    return weight * distance_score(miles)
