"""Cliff navigator -- finds safe wage transitions through benefits cliffs.

Analyzes the benefits cliff landscape for a household profile and
identifies wage targets where net income (wages + benefits - taxes)
is monotonically increasing. This lets the pathway engine route
career steps AROUND cliffs rather than into them.
"""

from pydantic import BaseModel

from app.modules.benefits.cliff_calculator import (
    WAGE_MAX,
    WAGE_MIN,
    WAGE_STEP,
    calculate_net_at_wage,
)
from app.modules.benefits.router import get_program_calculators
from app.modules.benefits.thresholds import HOURS_PER_YEAR
from app.modules.benefits.types import BenefitsProfile


class CliffZone(BaseModel):
    """A wage range where a benefits cliff causes net income to drop."""

    program: str
    cliff_start: float  # hourly wage where benefit begins dropping
    cliff_end: float  # hourly wage where net income recovers
    max_monthly_loss: float


class SafeWageTarget(BaseModel):
    """A wage that safely avoids all cliff zones."""

    wage: float
    net_monthly: float
    is_past_cliff: bool = False  # True if this wage is above a cliff recovery


def find_cliff_zones(profile: BenefitsProfile) -> list[CliffZone]:
    """Identify wage ranges where benefits cliffs reduce net income.

    Scans each enrolled program across the wage range to find where
    the program benefit drops, then identifies the recovery point.
    """
    if not profile.enrolled_programs:
        return []

    calculators = get_program_calculators()
    zones: list[CliffZone] = []

    for prog in profile.enrolled_programs:
        calc = calculators.get(prog)
        if calc is None:
            continue
        zone = _find_program_cliff(prog, calc, profile)
        if zone is not None:
            zones.append(zone)

    return sorted(zones, key=lambda z: z.cliff_start)


def _find_program_cliff(
    program: str,
    calc,
    profile: BenefitsProfile,
) -> CliffZone | None:
    """Find the cliff zone for a single program."""
    prev_benefit = None
    cliff_start = None
    max_loss = 0.0

    wage = WAGE_MIN
    while wage <= WAGE_MAX + 0.01:
        annual = wage * HOURS_PER_YEAR
        benefit = calc(annual, profile)

        if prev_benefit is not None and prev_benefit - benefit > 1.0:
            if cliff_start is None:
                cliff_start = round(wage - WAGE_STEP, 2)
            loss = prev_benefit - benefit
            if loss > max_loss:
                max_loss = loss

        prev_benefit = benefit
        wage = round(wage + WAGE_STEP, 2)

    if cliff_start is None:
        return None

    # Find recovery: where net income at cliff_start is exceeded
    net_at_start = calculate_net_at_wage(cliff_start, profile)
    cliff_end = cliff_start
    wage = round(cliff_start + WAGE_STEP, 2)
    while wage <= WAGE_MAX + 0.01:
        net = calculate_net_at_wage(wage, profile)
        if net >= net_at_start:
            cliff_end = wage
            break
        wage = round(wage + WAGE_STEP, 2)
    else:
        cliff_end = WAGE_MAX

    return CliffZone(
        program=program,
        cliff_start=cliff_start,
        cliff_end=round(cliff_end, 2),
        max_monthly_loss=round(max_loss, 2),
    )


def is_wage_safe(wage: float, zones: list[CliffZone]) -> bool:
    """Check if a wage avoids all cliff zones.

    A wage is safe if it is below all cliff starts or at/above
    all cliff ends (recovery points).
    """
    for zone in zones:
        if zone.cliff_start < wage < zone.cliff_end:
            return False
    return True


def find_safe_wage_targets(
    profile: BenefitsProfile,
    current_wage: float,
    step_size: float = 2.0,
) -> list[SafeWageTarget]:
    """Find wage targets that are safe landing points.

    Returns wages above current_wage where net income is higher than
    at the previous target and no cliff zone is active.
    """
    zones = find_cliff_zones(profile)
    targets: list[SafeWageTarget] = []

    current_net = calculate_net_at_wage(
        max(current_wage, WAGE_MIN), profile,
    )

    wage = round(current_wage + step_size, 2)
    prev_net = current_net

    while wage <= WAGE_MAX:
        net = calculate_net_at_wage(wage, profile)
        if net > prev_net and is_wage_safe(wage, zones):
            past_cliff = any(wage >= z.cliff_end for z in zones)
            targets.append(SafeWageTarget(
                wage=round(wage, 2),
                net_monthly=round(net, 2),
                is_past_cliff=past_cliff,
            ))
            prev_net = net
        wage = round(wage + step_size, 2)

    # Always include a high-wage target if none found
    if not targets:
        net = calculate_net_at_wage(WAGE_MAX, profile)
        targets.append(SafeWageTarget(
            wage=WAGE_MAX,
            net_monthly=round(net, 2),
            is_past_cliff=True,
        ))

    return targets
