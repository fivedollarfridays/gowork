"""Pathway engine -- orchestrates multi-step career trajectory generation.

Fuses barrier sequencer, benefits cliff calculator, and wage analysis
into ranked career pathways. Each pathway shows the JOURNEY: barrier
resolution order, safe wage targets, cliff warnings, and estimated
timeline from current state to target career.

Zero LLM calls. Fully deterministic.
"""

from app.modules.benefits.cliff_calculator import (
    WAGE_MAX,
    WAGE_MIN,
    calculate_net_at_wage,
)
from app.modules.benefits.types import BenefitsProfile
from app.modules.pathway.cliff_navigator import (
    CliffZone,
    find_cliff_zones,
    find_safe_wage_targets,
)
from app.modules.pathway.stage_builder import build_stages
from app.modules.pathway.types import (
    CareerPathway,
    CliffWarning,
    PathwayResult,
    PathwayStep,
)

# Pathway generation strategies
_STRATEGY_CONSERVATIVE = "conservative"  # Fewest barriers first, slow climb
_STRATEGY_AGGRESSIVE = "aggressive"  # High wage target, resolve all barriers
_STRATEGY_BALANCED = "balanced"  # Mix: safe progression with ambition

# Barrier impact on job accessibility (multiplier, 1.0 = no impact)
_BARRIER_JOB_PENALTY = {
    "criminal_record": 0.6,
    "credit": 0.8,
    "transportation": 0.7,
    "childcare": 0.85,
    "housing": 0.75,
    "health": 0.9,
    "training": 0.7,
}


def _estimate_jobs_at_wage(
    wage: float, barriers_remaining: list[str],
) -> int:
    """Estimate accessible jobs at a wage, penalized by active barriers."""
    # Base: more jobs at lower wages (entry-level more abundant)
    if wage <= 10.0:
        base = 15
    elif wage <= 14.0:
        base = 12
    elif wage <= 18.0:
        base = 8
    elif wage <= 22.0:
        base = 5
    else:
        base = 3

    # Apply barrier penalties
    factor = 1.0
    for b in barriers_remaining:
        factor *= _BARRIER_JOB_PENALTY.get(b, 0.9)

    return max(1, int(base * factor))


def _attach_cliff_warnings(
    steps: list[PathwayStep],
    zones: list[CliffZone],
) -> list[PathwayStep]:
    """Annotate steps with cliff warnings where applicable."""
    result: list[PathwayStep] = []
    for step in steps:
        warnings: list[CliffWarning] = []
        for zone in zones:
            if zone.cliff_start <= step.target_wage <= zone.cliff_end:
                warnings.append(CliffWarning(
                    program=zone.program,
                    cliff_wage=zone.cliff_start,
                    monthly_loss=zone.max_monthly_loss,
                    severity=_severity_label(zone.max_monthly_loss),
                ))
        updated = step.model_copy(update={"cliff_warnings": warnings})
        result.append(updated)
    return result


def _severity_label(monthly_loss: float) -> str:
    """Classify cliff severity."""
    if monthly_loss >= 200:
        return "severe"
    if monthly_loss >= 50:
        return "moderate"
    return "mild"


def _compute_viability(
    steps: list[PathwayStep],
    barrier_count: int,
    total_weeks: int,
) -> float:
    """Score pathway viability 0.0-1.0.

    Factors: fewer barriers = better, shorter timeline = better,
    more jobs accessible = better, fewer cliff warnings = better.
    """
    if not steps:
        return 0.0

    # Barrier penalty: each barrier reduces viability
    barrier_penalty = min(barrier_count * 0.08, 0.4)

    # Timeline penalty: long timelines reduce viability
    timeline_penalty = min(total_weeks * 0.005, 0.3)

    # Job accessibility bonus
    avg_jobs = sum(s.jobs_accessible for s in steps) / len(steps)
    job_bonus = min(avg_jobs / 15.0, 0.2)

    # Cliff warning penalty
    cliff_count = sum(len(s.cliff_warnings) for s in steps)
    cliff_penalty = min(cliff_count * 0.05, 0.15)

    score = 0.85 - barrier_penalty - timeline_penalty + job_bonus - cliff_penalty
    return max(0.05, min(1.0, round(score, 3)))


def _enrich_steps(
    steps: list[PathwayStep],
    barrier_ids: list[str],
    profile: BenefitsProfile,
) -> list[PathwayStep]:
    """Add net income and refined job counts to raw steps."""
    enriched: list[PathwayStep] = []
    remaining_barriers = list(barrier_ids)
    for step in steps:
        for b in step.barriers_to_resolve:
            if b in remaining_barriers:
                remaining_barriers.remove(b)
        net = calculate_net_at_wage(step.target_wage, profile)
        updated = step.model_copy(update={
            "net_monthly_income": round(net, 2),
            "jobs_accessible": _estimate_jobs_at_wage(
                step.target_wage, remaining_barriers,
            ),
        })
        enriched.append(updated)
    return enriched


def _build_pathway(
    name: str,
    pathway_id: str,
    barrier_ids: list[str],
    profile: BenefitsProfile,
    current_wage: float,
    wage_step: float,
) -> CareerPathway:
    """Build a single pathway with given wage step size."""
    targets = find_safe_wage_targets(profile, current_wage, step_size=wage_step)
    zones = find_cliff_zones(profile)

    wage_list = [t.wage for t in targets]
    jobs_map = {w: _estimate_jobs_at_wage(w, barrier_ids) for w in wage_list}
    steps = build_stages(barrier_ids, wage_list, jobs_map)

    enriched = _enrich_steps(steps, barrier_ids, profile)
    enriched = _attach_cliff_warnings(enriched, zones)

    total_weeks = enriched[-1].estimated_weeks if enriched else 0
    final_wage = enriched[-1].target_wage if enriched else current_wage
    final_net = calculate_net_at_wage(max(final_wage, WAGE_MIN), profile)
    viability = _compute_viability(enriched, len(barrier_ids), total_weeks)

    return CareerPathway(
        pathway_id=pathway_id,
        name=name,
        steps=enriched,
        total_weeks=total_weeks,
        final_wage=final_wage,
        final_net_monthly=round(final_net, 2),
        viability_score=viability,
    )


def generate_pathways(
    barrier_ids: list[str],
    benefits_profile: BenefitsProfile,
    current_wage: float,
) -> PathwayResult:
    """Generate ranked career pathways for a user profile.

    Produces multiple pathway strategies (conservative, balanced,
    aggressive) and ranks them by viability score.

    Args:
        barrier_ids: Active barrier category IDs.
        benefits_profile: Household benefits profile for cliff analysis.
        current_wage: Current hourly wage (0.0 if unemployed).

    Returns:
        PathwayResult with ranked pathways and current state info.
    """
    effective_wage = max(current_wage, WAGE_MIN)
    current_net = calculate_net_at_wage(effective_wage, benefits_profile)

    strategies = [
        ("Conservative path", "conservative", 4.0),
        ("Balanced path", "balanced", 3.0),
        ("Aggressive path", "aggressive", 2.0),
    ]

    pathways: list[CareerPathway] = []
    for name, pid, step in strategies:
        pathway = _build_pathway(
            name, pid, barrier_ids, benefits_profile,
            current_wage, wage_step=step,
        )
        pathways.append(pathway)

    # Sort by viability descending
    pathways.sort(key=lambda p: p.viability_score, reverse=True)

    return PathwayResult(
        pathways=pathways,
        current_wage=current_wage,
        current_net_monthly=round(current_net, 2),
        barriers_active=list(barrier_ids),
    )
