"""PVS (Practical Value Score) composite scorer.

Replaces 3-bucket system with a single ranked list scored by:
  PVS = 0.35 * earnings + 0.25 * proximity + 0.20 * time_fit + 0.20 * barrier_compat
"""

from app.modules.matching.proximity_scorer import score_proximity
from app.modules.matching.salary_parser import SalaryInfo, extract_salary, score_earnings
from app.modules.matching.time_fit_scorer import score_time_fit
from app.modules.matching.types import (
    AvailableHours,
    BarrierType,
    MatchBucket,
    ScoredJobMatch,
)

# PVS component weights
W_EARNINGS = 0.35
W_PROXIMITY = 0.25
W_TIME_FIT = 0.20
W_BARRIER_COMPAT = 0.20

# No-pay ceiling: jobs without disclosed salary can never exceed this
NO_PAY_CEILING = 0.25

# Sentinel: distinguishes "not yet parsed" from "parsed but no salary found"
_NOT_PARSED = object()

# Barrier compatibility
_CREDIT_BLOCKED_SCORE = 0.2
_RECORD_BLOCKED_SCORE = 0.2
_RECORD_UNKNOWN_SCORE = 0.5
_RECORD_ELIGIBLE_SCORE = 0.8


def _score_barrier_compat(job: dict, barriers: list[BarrierType]) -> float:
    """Score barrier compatibility (0.0-1.0). Credit: 0.2 if blocked.
    Record: fair_chance→1.0, eligible→0.8, blocked→0.2, unknown→0.5.
    """
    score = 1.0
    if job.get("credit_blocked") and BarrierType.CREDIT in barriers:
        score = min(score, _CREDIT_BLOCKED_SCORE)
    if BarrierType.CRIMINAL_RECORD in barriers:
        if "record_eligible" in job:
            if not job["record_eligible"]:
                score = min(score, _RECORD_BLOCKED_SCORE)
            elif job.get("fair_chance"):
                pass  # 1.0 — no penalty
            else:
                score = min(score, _RECORD_ELIGIBLE_SCORE)
        else:
            score = min(score, _RECORD_UNKNOWN_SCORE)
    return score


def _format_pay_range(salary: SalaryInfo | None) -> str | None:
    """Format salary info into a human-readable pay range string."""
    if salary is None:
        return None
    if salary.is_range:
        return salary.raw_text
    return f"${salary.hourly_rate:.2f}/hr"


def compute_pvs(
    job: dict,
    user_zip: str,
    transit_dependent: bool,
    schedule_type: AvailableHours,
    barriers: list[BarrierType],
    salary: SalaryInfo | None | object = _NOT_PARSED,
) -> float:
    """Compute Practical Value Score (0.0-1.0) for a job.

    No-pay jobs are capped at NO_PAY_CEILING regardless of other factors.
    Pass pre-extracted salary to avoid redundant parsing.
    """
    if salary is _NOT_PARSED:
        salary = extract_salary(job.get("description"))

    earnings = score_earnings(salary)
    proximity = score_proximity(user_zip, job.get("location", ""), transit_dependent)
    time_fit = score_time_fit(job, schedule_type, barriers)
    barrier_compat = _score_barrier_compat(job, barriers)

    pvs = (
        W_EARNINGS * earnings
        + W_PROXIMITY * proximity
        + W_TIME_FIT * time_fit
        + W_BARRIER_COMPAT * barrier_compat
    )
    pvs = max(0.0, min(1.0, pvs))

    if salary is None:
        pvs = min(pvs, NO_PAY_CEILING)

    return round(pvs, 3)


def _build_pvs_reason(job: dict, salary: SalaryInfo | None) -> str:
    """Generate match reason for PVS-ranked job."""
    parts: list[str] = []
    if job.get("industry_match"):
        parts.append("Matches your target industry")
    if salary:
        parts.append(f"Pays ${salary.hourly_rate:.2f}/hr")
    if not parts:
        parts.append("Entry-level opportunity")
    return "; ".join(parts)


def rank_all_jobs(
    jobs: list[dict],
    user_zip: str,
    transit_dependent: bool,
    schedule_type: AvailableHours,
    barriers: list[BarrierType],
) -> list[ScoredJobMatch]:
    """Score all jobs with PVS, return flat list sorted descending. No caps."""
    results: list[ScoredJobMatch] = []

    for job in jobs:
        salary = extract_salary(job.get("description"))
        pvs = compute_pvs(job, user_zip, transit_dependent, schedule_type, barriers, salary=salary)
        reason = _build_pvs_reason(job, salary)
        is_credit_blocked = job.get("credit_blocked", False)

        match = ScoredJobMatch(
            title=job["title"],
            company=job.get("company"),
            location=job.get("location"),
            url=job.get("url"),
            source=job.get("source"),
            credit_check_required=job.get("credit_check", "unknown"),
            transit_accessible=job.get("transit_accessible", False),
            fair_chance=job.get("fair_chance", False),
            record_eligible=job.get("record_eligible", True),
            background_check_timing=job.get("background_check_timing"),
            record_note=job.get("record_note"),
            relevance_score=pvs,
            match_reason=reason,
            pay_range=_format_pay_range(salary),
            bucket=MatchBucket.AFTER_REPAIR if is_credit_blocked else MatchBucket.STRONG,
        )
        results.append(match)

    results.sort(key=lambda m: m.relevance_score, reverse=True)
    return results
