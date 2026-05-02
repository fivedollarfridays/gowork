"""PVS (Practical Value Score) composite scorer.

Replaces 3-bucket system with a single ranked list.  Default weights
when no resume profile is present:
  PVS = 0.35 net_income + 0.25 proximity + 0.20 time_fit + 0.20 barrier_compat

When a resume profile IS present (the assessment carried resume_text
through to ScoringContext.resume_profile), a fifth term is added and
the others are rebalanced:
  PVS = 0.20 net_income + 0.15 proximity + 0.15 time_fit + 0.15 barrier_compat
       + 0.35 resume_match
"""

from collections.abc import Sequence

from app.modules.benefits.cliff_calculator import calculate_net_at_wage, classify_cliff_severity
from app.modules.benefits.router import get_program_calculators, get_sum_program_benefits
from app.modules.benefits.thresholds import HOURS_PER_YEAR, MONTHS_PER_YEAR
from app.modules.benefits.types import BenefitsProfile
from app.modules.matching.commute_estimator import estimate_commute
from app.modules.matching.proximity_scorer import score_proximity
from app.modules.matching.relevance_scorer import (
    ResumeProfile,
    matched_signal_summary,
    score_resume_match,
    score_resume_match_breakdown,
)
from app.modules.matching.salary_parser import (
    EARNINGS_BENCHMARK,
    SalaryInfo,
    extract_salary,
    score_earnings,
)
from app.modules.matching.time_fit_scorer import score_time_fit
from app.modules.matching.types import (
    BarrierType,
    CliffImpact,
    MatchBucket,
    ScoredJobMatch,
    ScoringContext,
)

# PVS component weights — no-resume path
W_NET_INCOME = 0.35
W_PROXIMITY = 0.25
W_TIME_FIT = 0.20
W_BARRIER_COMPAT = 0.20

# PVS component weights — with-resume path (drives ranking by fit)
WR_NET_INCOME = 0.20
WR_PROXIMITY = 0.15
WR_TIME_FIT = 0.15
WR_BARRIER_COMPAT = 0.15
WR_RESUME_MATCH = 0.35

# No-pay penalty: jobs without disclosed salary are scaled down but still
# differentiate on proximity, time fit, and barrier compatibility
NO_PAY_MULTIPLIER = 0.55

# Sentinel: distinguishes "not yet parsed" from "parsed but no salary found"
class _NotParsedType:
    """Sentinel type for unparsed salary."""

_NOT_PARSED = _NotParsedType()

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


def _score_net_income(salary: SalaryInfo, profile: BenefitsProfile) -> float:
    """Score 0.0-1.0 based on net income (wages + benefits - taxes)."""
    net_monthly = calculate_net_at_wage(salary.hourly_rate, profile)
    net_annual = net_monthly * MONTHS_PER_YEAR
    score = min(net_annual / EARNINGS_BENCHMARK, 1.0)
    return max(score, 0.15)  # same disclosed floor as gross scoring


def _affected_programs(
    annual_job: float, annual_current: float, profile: BenefitsProfile,
) -> list[str]:
    """List programs that decrease going from current to job income."""
    calculators = get_program_calculators()
    return [
        prog for prog in profile.enrolled_programs
        if (calc := calculators.get(prog))
        and calc(annual_job, profile) < calc(annual_current, profile)
    ]


def _current_net(profile: BenefitsProfile) -> float:
    """Net monthly income at current wage."""
    if profile.current_monthly_income <= 0:
        return 0.0
    hourly = profile.current_monthly_income * MONTHS_PER_YEAR / HOURS_PER_YEAR
    return calculate_net_at_wage(hourly, profile)


def _compute_cliff_impact(
    salary: SalaryInfo, profile: BenefitsProfile,
    current_benefits: float, current_net_monthly: float,
    job_net_monthly: float = 0.0,
) -> CliffImpact:
    """Calculate benefits cliff impact for a job at a given wage."""
    annual_job = salary.hourly_rate * HOURS_PER_YEAR
    annual_current = profile.current_monthly_income * MONTHS_PER_YEAR
    sum_fn = get_sum_program_benefits()
    benefits_change = round(
        sum_fn(annual_job, profile) - current_benefits, 2,
    )
    net_change = round(job_net_monthly - current_net_monthly, 2)
    has_cliff = benefits_change < -1.0
    return CliffImpact(
        benefits_change=benefits_change,
        net_monthly_change=net_change,
        has_cliff=has_cliff,
        severity=classify_cliff_severity(abs(benefits_change)) if has_cliff else None,
        affected_programs=_affected_programs(annual_job, annual_current, profile),
    )


def _format_pay_range(salary: SalaryInfo | None) -> str | None:
    """Format salary info into a human-readable pay range string."""
    if salary is None:
        return None
    if salary.is_range:
        return salary.raw_text
    return f"${salary.hourly_rate:.2f}/hr"


def _compute_resume_match(
    job: dict, ctx: ScoringContext,
) -> tuple[float, list[str]]:
    """Project the resume profile (if any) into a job-match score."""
    profile = ctx.resume_profile
    if not isinstance(profile, ResumeProfile):
        return 0.0, []
    return score_resume_match(job, profile)


def _compute_resume_breakdown(job: dict, ctx: ScoringContext) -> dict | None:
    """Return the per-factor breakdown when a resume profile is present."""
    profile = ctx.resume_profile
    if not isinstance(profile, ResumeProfile):
        return None
    _, _, breakdown = score_resume_match_breakdown(job, profile)
    return breakdown


def _job_data_source(job: dict) -> list[str]:
    """Build provenance list from job dict (Pattern 13)."""
    parts: list[str] = []
    src = job.get("source") or "unknown"
    parts.append(str(src))
    if job.get("city_tag"):
        parts.append(f"city:{job['city_tag']}")
    if job.get("ingested_at"):
        parts.append(f"ingested:{job['ingested_at']}")
    return parts


def compute_pvs(
    job: dict,
    ctx: ScoringContext,
    salary: SalaryInfo | None | _NotParsedType = _NOT_PARSED,
) -> float:
    """Compute Practical Value Score (0.0-1.0) for a job.

    Uses net income (wages + benefits - taxes) when benefits_profile is
    available with enrolled programs.  Falls back to gross earnings otherwise.
    No-pay jobs are penalised by NO_PAY_MULTIPLIER.

    When ``ctx.resume_profile`` is set, a fifth term (resume_match) is
    blended in with WR_* weights so jobs that line up with the user's
    skills/family/industry rank higher.  This is the fix for the
    "every job scores 0.363" symptom that affected every same-city
    listing without resume signal.
    """
    if salary is _NOT_PARSED:
        salary = extract_salary(job.get("description"))

    bp = ctx.benefits_profile
    if salary and bp and bp.enrolled_programs:
        income_score = _score_net_income(salary, bp)
    else:
        income_score = score_earnings(salary)

    proximity = score_proximity(ctx.user_zip, job.get("location", ""), ctx.transit_dependent)
    time_fit = score_time_fit(job, ctx.schedule_type, ctx.barriers)
    barrier_compat = _score_barrier_compat(job, ctx.barriers)

    has_resume = isinstance(ctx.resume_profile, ResumeProfile)
    if has_resume:
        resume_score, _ = _compute_resume_match(job, ctx)
        pvs = (
            WR_NET_INCOME * income_score
            + WR_PROXIMITY * proximity
            + WR_TIME_FIT * time_fit
            + WR_BARRIER_COMPAT * barrier_compat
            + WR_RESUME_MATCH * resume_score
        )
    else:
        pvs = (
            W_NET_INCOME * income_score
            + W_PROXIMITY * proximity
            + W_TIME_FIT * time_fit
            + W_BARRIER_COMPAT * barrier_compat
        )
    pvs = max(0.0, min(1.0, pvs))

    if salary is None:
        pvs *= NO_PAY_MULTIPLIER

    return round(pvs, 3)


def _build_pvs_reason(
    job: dict, salary: SalaryInfo | None,
    target_industries: Sequence[str] = (),
    resume_keywords: Sequence[str] = (),
    resume_signals: Sequence[str] = (),
) -> str:
    """Generate a match reason for a PVS-ranked job.

    Priority order for the headline phrase:
      1. Resume signals (skills + family + cert) — most specific.
      2. Target industries selected in the wizard.
      3. Pre-existing resume_keyword hits (legacy path).
      4. Disclosed pay band.
      5. Generic "entry-level opportunity" fallback.
    """
    parts: list[str] = []
    searchable = f"{job.get('title', '')} {job.get('description', '')}".lower()

    if resume_signals:
        summary = matched_signal_summary(resume_signals)
        if summary:
            parts.append(f"Matches your {summary}")
    if job.get("industry_match") and target_industries:
        matched = next((i for i in target_industries if i.lower() in searchable), None)
        parts.append(f"Matches your target: {matched}" if matched else "Matches your target industry")
    elif job.get("industry_match") and not parts:
        parts.append("Matches your target industry")
    if resume_keywords and not resume_signals:
        matched_kw = next((kw for kw in resume_keywords if kw.lower() in searchable), None)
        if matched_kw:
            parts.append(f"Matches your {matched_kw} experience")
    if salary:
        parts.append(f"Pays ${salary.hourly_rate:.2f}/hr")
    if not parts:
        parts.append("Entry-level opportunity")
    return "; ".join(parts)


def _cliff_for_job(
    salary: SalaryInfo | None, benefits_profile: BenefitsProfile | None,
    current_benefits: float, current_net_monthly: float,
) -> CliffImpact | None:
    """Compute cliff impact for a single job, or None if not applicable."""
    if not (salary and benefits_profile and benefits_profile.enrolled_programs):
        return None
    job_net = calculate_net_at_wage(salary.hourly_rate, benefits_profile)
    return _compute_cliff_impact(
        salary, benefits_profile, current_benefits, current_net_monthly,
        job_net_monthly=job_net,
    )


def _build_match(
    job: dict, salary: SalaryInfo | None, pvs: float,
    benefits_profile: BenefitsProfile | None,
    current_benefits: float = 0.0, current_net_monthly: float = 0.0,
    target_industries: Sequence[str] = (),
    resume_keywords: Sequence[str] = (),
    user_zip: str = "",
    resume_signals: Sequence[str] = (),
    score_breakdown: dict | None = None,
) -> ScoredJobMatch:
    """Build a ScoredJobMatch from a raw job dict."""
    transit_info = job.get("transit_info")
    return ScoredJobMatch(
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
        match_reason=_build_pvs_reason(
            job, salary, target_industries, resume_keywords, resume_signals,
        ),
        pay_range=_format_pay_range(salary),
        bucket=MatchBucket.AFTER_REPAIR if job.get("credit_blocked") else MatchBucket.STRONG,
        cliff_impact=_cliff_for_job(salary, benefits_profile, current_benefits, current_net_monthly),
        transit_info=transit_info,
        commute_estimate=estimate_commute(user_zip, job.get("location", ""), transit_info),
        score_breakdown=score_breakdown,
        data_source=_job_data_source(job),
    )


def rank_all_jobs(
    jobs: list[dict],
    ctx: ScoringContext,
) -> list[ScoredJobMatch]:
    """Score all jobs with PVS, return flat list sorted descending. No caps."""
    bp = ctx.benefits_profile
    # Pre-compute current-wage values (constant across all jobs)
    cur_benefits = cur_net = 0.0
    if bp and bp.enrolled_programs:
        annual_current = bp.current_monthly_income * MONTHS_PER_YEAR
        sum_fn = get_sum_program_benefits()
        cur_benefits = sum_fn(annual_current, bp)
        cur_net = _current_net(bp)

    results: list[ScoredJobMatch] = []
    for job in jobs:
        salary = extract_salary(job.get("description"))
        pvs = compute_pvs(job, ctx, salary=salary)
        _, resume_signals = _compute_resume_match(job, ctx)
        breakdown = _compute_resume_breakdown(job, ctx)
        results.append(_build_match(
            job, salary, pvs, bp, cur_benefits, cur_net,
            target_industries=ctx.target_industries,
            resume_keywords=ctx.resume_keywords,
            user_zip=ctx.user_zip,
            resume_signals=resume_signals,
            score_breakdown=breakdown,
        ))
    results.sort(key=lambda m: m.relevance_score, reverse=True)
    return results
