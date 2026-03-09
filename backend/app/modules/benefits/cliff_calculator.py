"""Benefits cliff calculator — computes net income across wage levels."""

import logging

from app.modules.benefits.types import (
    BenefitsProfile,
    CliffAnalysis,
    CliffPoint,
    CliffSeverity,
    CliffType,
    ProgramBenefit,
    WageStep,
)
from app.modules.benefits.thresholds import (
    ALL_KIDS_FPL_PCT,
    AMI_MONTGOMERY_2026,
    CHILDCARE_SMI_LIMIT_PCT,
    FICA_RATE,
    FPL_2026,
    HOURS_PER_YEAR,
    LIHEAP_FPL_LIMIT_PCT,
    MONTHS_PER_YEAR,
    SECTION_8_AMI_LIMIT_PCT,
    SMI_2026,
    TAX_BRACKETS,
    TANF_MAX_MONTHLY,
)
from app.modules.benefits.program_calculators import (
    PROGRAM_CALCULATORS,
    sum_program_benefits,
)

logger = logging.getLogger(__name__)

WAGE_MIN = 8.0
WAGE_MAX = 25.0
WAGE_STEP = 0.50
_WAGE_STEP_COUNT = int((WAGE_MAX - WAGE_MIN) / WAGE_STEP) + 1


def calculate_cliff_analysis(profile: BenefitsProfile) -> CliffAnalysis:
    """Compute net income at each wage step and identify cliff points."""
    wage_steps = _build_wage_steps(profile)
    cliff_points = _detect_cliffs(wage_steps, profile)
    programs = _build_program_list(profile)
    current_net = _compute_current_net(profile)

    worst_cliff_wage = None
    if cliff_points:
        worst = max(cliff_points, key=lambda c: c.monthly_loss)
        worst_cliff_wage = worst.hourly_wage

    recovery_wage = _find_recovery_wage(wage_steps, cliff_points)

    return CliffAnalysis(
        wage_steps=wage_steps,
        cliff_points=cliff_points,
        current_net_monthly=round(current_net, 2),
        programs=programs,
        worst_cliff_wage=worst_cliff_wage,
        recovery_wage=recovery_wage,
    )


def calculate_net_at_wage(hourly_wage: float, profile: BenefitsProfile) -> float:
    """Calculate monthly net income at a given hourly wage."""
    annual = hourly_wage * HOURS_PER_YEAR
    gross_monthly = annual / MONTHS_PER_YEAR
    benefits = _total_benefits(hourly_wage, profile)
    taxes = _estimate_taxes(annual)
    return gross_monthly - taxes / MONTHS_PER_YEAR + benefits


def classify_cliff_severity(monthly_loss: float) -> CliffSeverity:
    """Classify cliff severity by monthly dollar loss."""
    if monthly_loss >= 200:
        return CliffSeverity.SEVERE
    if monthly_loss >= 50:
        return CliffSeverity.MODERATE
    return CliffSeverity.MILD


def _build_wage_steps(profile: BenefitsProfile) -> list[WageStep]:
    steps: list[WageStep] = []
    for i in range(_WAGE_STEP_COUNT):
        wage = WAGE_MIN + i * WAGE_STEP
        annual = wage * HOURS_PER_YEAR
        gross_monthly = annual / MONTHS_PER_YEAR
        benefits = _total_benefits(wage, profile)
        taxes = _estimate_taxes(annual)
        net = gross_monthly - taxes / MONTHS_PER_YEAR + benefits
        steps.append(WageStep(
            wage=round(wage, 2),
            gross_monthly=round(gross_monthly, 2),
            benefits_total=round(benefits, 2),
            net_monthly=round(net, 2),
        ))
    return steps


def _total_benefits(hourly_wage: float, profile: BenefitsProfile) -> float:
    """Sum enrolled-program benefits at a given hourly wage."""
    return sum_program_benefits(hourly_wage * HOURS_PER_YEAR, profile)


def _estimate_taxes(annual_income: float) -> float:
    fica = annual_income * FICA_RATE
    income_tax = 0.0
    remaining = annual_income
    prev_bracket = 0.0
    for bracket_top, rate in TAX_BRACKETS:
        taxable = min(remaining, bracket_top - prev_bracket)
        if taxable <= 0:
            break
        income_tax += taxable * rate
        remaining -= taxable
        prev_bracket = bracket_top
    return fica + income_tax


def _detect_cliffs(
    steps: list[WageStep], profile: BenefitsProfile,
) -> list[CliffPoint]:
    cliffs: list[CliffPoint] = []
    for i in range(1, len(steps)):
        drop = steps[i - 1].net_monthly - steps[i].net_monthly
        if drop > 1.0:
            lost = _identify_lost_program(steps[i - 1], steps[i], profile)
            cliffs.append(CliffPoint(
                hourly_wage=steps[i].wage,
                annual_income=steps[i].wage * HOURS_PER_YEAR,
                net_monthly_income=steps[i].net_monthly,
                lost_program=lost,
                monthly_loss=round(drop, 2),
                severity=classify_cliff_severity(drop),
            ))
    return cliffs


def _identify_lost_program(
    before: WageStep, after: WageStep, profile: BenefitsProfile,
) -> str:
    biggest_drop = 0.0
    lost = "Unknown"
    for prog in profile.enrolled_programs:
        calc = PROGRAM_CALCULATORS[prog]
        before_val = calc(before.wage * HOURS_PER_YEAR, profile)
        after_val = calc(after.wage * HOURS_PER_YEAR, profile)
        drop = before_val - after_val
        if drop > biggest_drop:
            biggest_drop = drop
            lost = prog
    return lost


def _build_program_list(profile: BenefitsProfile) -> list[ProgramBenefit]:
    programs: list[ProgramBenefit] = []
    annual = profile.current_monthly_income * MONTHS_PER_YEAR
    for prog in profile.enrolled_programs:
        calc = PROGRAM_CALCULATORS[prog]
        value = calc(annual, profile)
        phase_out = _get_phase_out(prog, profile)
        programs.append(ProgramBenefit(
            program=prog,
            monthly_value=round(value, 2),
            eligible=value > 0,
            phase_out_start=phase_out[0],
            phase_out_end=phase_out[1],
            cliff_type=phase_out[2],
        ))
    return programs


def _get_phase_out(
    program: str, profile: BenefitsProfile,
) -> tuple[float, float, CliffType]:
    hs = min(profile.household_size, 8)
    fpl = FPL_2026[hs]
    if program == "SNAP":
        return (fpl * 0.80, fpl * 1.30, CliffType.GRADUAL)
    if program == "TANF":
        limit = TANF_MAX_MONTHLY.get(hs, 215) * MONTHS_PER_YEAR * 0.75
        return (limit * 0.5, limit, CliffType.HARD)
    if program == "ALL_Kids":
        return (fpl * 2.0, fpl * ALL_KIDS_FPL_PCT, CliffType.HARD)
    if program == "Childcare_Subsidy":
        smi = SMI_2026[hs]
        return (smi * 0.50, smi * CHILDCARE_SMI_LIMIT_PCT, CliffType.GRADUAL)
    if program == "Section_8":
        ami = AMI_MONTGOMERY_2026[hs]
        return (ami * 0.30, ami * SECTION_8_AMI_LIMIT_PCT, CliffType.GRADUAL)
    if program == "LIHEAP":
        return (fpl * 1.0, fpl * LIHEAP_FPL_LIMIT_PCT, CliffType.HARD)
    logger.warning("Unknown program in phase-out calculation: %s", program)
    return (0, 0, CliffType.HARD)


def _compute_current_net(profile: BenefitsProfile) -> float:
    if profile.current_monthly_income <= 0:
        return 0.0
    hourly = profile.current_monthly_income * MONTHS_PER_YEAR / HOURS_PER_YEAR
    return calculate_net_at_wage(hourly, profile)


def _find_recovery_wage(
    steps: list[WageStep], cliffs: list[CliffPoint],
) -> float | None:
    """Find the first wage where net income recovers to pre-cliff peak."""
    if not cliffs:
        return None
    first_cliff_wage = min(c.hourly_wage for c in cliffs)
    pre_cliff_peak = max(
        s.net_monthly for s in steps if s.wage < first_cliff_wage
    )
    for step in steps:
        if step.wage >= first_cliff_wage and step.net_monthly >= pre_cliff_peak:
            return step.wage
    return None
