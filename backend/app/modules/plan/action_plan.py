"""Action plan timeline builder — synthesizes all module outputs into a phased plan.

Produces a 5-phase timeline:
  1. Week 1-2: Immediate Actions
  2. Month 1: Foundations
  3. Month 2-3: Building
  4. Month 3-6: Advancement
  5. Month 6-12: Stability
"""

from datetime import date

from app.modules.plan.phase_generators import (
    generate_benefits_actions,
    generate_career_center_action,
    generate_cliff_actions,
    generate_credit_actions,
    generate_criminal_actions,
    generate_job_actions,
    generate_wioa_actions,
)
from app.modules.plan.types import ActionItem, ActionPlan, TimelinePhase

# Re-export types for convenience
from app.modules.plan.types import ActionCategory  # noqa: F401

# Phase definitions: (id, label, start_day, end_day)
_PHASE_DEFS: list[tuple[str, str, int, int]] = [
    ("week_1_2", "Week 1-2: Immediate Actions", 0, 14),
    ("month_1", "Month 1: Foundations", 14, 30),
    ("month_2_3", "Month 2-3: Building", 30, 90),
    ("month_3_6", "Month 3-6: Advancement", 90, 180),
    ("month_6_12", "Month 6-12: Stability", 180, 365),
]


def _empty_phases() -> list[TimelinePhase]:
    return [
        TimelinePhase(phase_id=pid, label=label, start_day=s, end_day=e)
        for pid, label, s, e in _PHASE_DEFS
    ]


def _populate_phases(phase_map: dict[str, TimelinePhase], **kwargs) -> None:
    """Collect actions from all generators and place into phases."""
    week1 = phase_map["week_1_2"]
    week1.actions.append(generate_career_center_action())
    week1.actions.extend(generate_job_actions(kwargs.get("strong_matches") or []))
    week1.actions.extend(generate_benefits_actions(
        kwargs.get("benefits_eligibility"), kwargs.get("enrolled_programs") or [],
    ))
    week1.actions.extend(generate_wioa_actions(kwargs.get("wioa_eligibility")))

    for phase_id, action in generate_criminal_actions(kwargs.get("barriers") or []):
        phase_map[phase_id].actions.append(action)
    for phase_id, action in generate_credit_actions(kwargs.get("credit_result")):
        phase_map[phase_id].actions.append(action)
    phase_map["month_6_12"].actions.extend(generate_cliff_actions(kwargs.get("cliff_analysis")))


def build_action_plan(
    *,
    strong_matches: list | None = None,
    benefits_eligibility=None,
    enrolled_programs: list[str] | None = None,
    wioa_eligibility=None,
    cliff_analysis=None,
    credit_result: dict | None = None,
    barriers: list | None = None,
    assessment_date: date,
) -> ActionPlan:
    """Build a phased action plan from all module outputs."""
    phases = _empty_phases()
    phase_map = {p.phase_id: p for p in phases}
    _populate_phases(
        phase_map,
        strong_matches=strong_matches, benefits_eligibility=benefits_eligibility,
        enrolled_programs=enrolled_programs, wioa_eligibility=wioa_eligibility,
        cliff_analysis=cliff_analysis, credit_result=credit_result, barriers=barriers,
    )
    total = sum(len(p.actions) for p in phases)
    return ActionPlan(assessment_date=assessment_date.isoformat(), phases=phases, total_actions=total)
