"""Per-program benefit calculators for Alabama benefit programs."""

from app.modules.benefits.types import BenefitsProfile
from app.modules.benefits.thresholds import (
    ALL_KIDS_FPL_PCT,
    AMI_MONTGOMERY_2026,
    CHILDCARE_COPAY_TIERS,
    CHILDCARE_MONTHLY_COST,
    CHILDCARE_SMI_LIMIT_PCT,
    FAIR_MARKET_RENT_2BR,
    FPL_2026,
    LIHEAP_AVG_MONTHLY,
    LIHEAP_FPL_LIMIT_PCT,
    MEDICAID_CHILD_VALUE,
    MONTHS_PER_YEAR,
    SECTION_8_AMI_LIMIT_PCT,
    SECTION_8_RENT_PCT,
    SMI_2026,
    SNAP_INCOME_DEDUCTION_RATE,
    SNAP_MAX_BENEFIT,
    SNAP_STANDARD_DEDUCTION,
    TANF_MAX_MONTHLY,
)


def calc_snap(annual_income: float, profile: BenefitsProfile) -> float:
    """SNAP (Food Stamps): 130% FPL gross, gradual phase-out."""
    hs = min(profile.household_size, 8)
    fpl = FPL_2026[hs]
    if annual_income > fpl * 1.30:
        return 0.0
    monthly_income = annual_income / MONTHS_PER_YEAR
    std_ded = SNAP_STANDARD_DEDUCTION[hs]
    net_income = max(monthly_income - std_ded, 0)
    benefit = SNAP_MAX_BENEFIT[hs] - net_income * SNAP_INCOME_DEDUCTION_RATE
    return max(benefit, 0.0)


def calc_tanf(annual_income: float, profile: BenefitsProfile) -> float:
    """TANF: very low Alabama benefits, hard cutoff."""
    hs = min(profile.household_size, 8)
    max_benefit = TANF_MAX_MONTHLY.get(hs, 215)
    income_limit = max_benefit * MONTHS_PER_YEAR * 0.75
    if annual_income > income_limit:
        return 0.0
    return max_benefit


def calc_medicaid(annual_income: float, profile: BenefitsProfile) -> float:
    """Medicaid adults: Alabama did NOT expand — not eligible."""
    return 0.0


def calc_all_kids(annual_income: float, profile: BenefitsProfile) -> float:
    """ALL Kids (Medicaid for children): 317% FPL."""
    hs = min(profile.household_size, 8)
    fpl = FPL_2026[hs]
    children = profile.dependents_under_6 + profile.dependents_6_to_17
    if children == 0 or annual_income > fpl * ALL_KIDS_FPL_PCT:
        return 0.0
    return MEDICAID_CHILD_VALUE * children


def calc_childcare(annual_income: float, profile: BenefitsProfile) -> float:
    """Childcare subsidy: 85% SMI, copay scale."""
    if profile.dependents_under_6 == 0:
        return 0.0
    hs = min(profile.household_size, 8)
    smi = SMI_2026[hs]
    if annual_income > smi * CHILDCARE_SMI_LIMIT_PCT:
        return 0.0
    total_cost = CHILDCARE_MONTHLY_COST * profile.dependents_under_6
    income_pct = annual_income / smi if smi > 0 else 0
    copay_pct = CHILDCARE_COPAY_TIERS[-1][1]  # default to last tier
    for threshold, pct in CHILDCARE_COPAY_TIERS:
        if income_pct <= threshold:
            copay_pct = pct
            break
    copay = total_cost * copay_pct
    return max(total_cost - copay, 0.0)


def calc_section_8(annual_income: float, profile: BenefitsProfile) -> float:
    """Section 8 Housing: 50% AMI, 30% income toward rent."""
    hs = min(profile.household_size, 8)
    ami = AMI_MONTGOMERY_2026[hs]
    if annual_income > ami * SECTION_8_AMI_LIMIT_PCT:
        return 0.0
    monthly_income = annual_income / MONTHS_PER_YEAR
    tenant_rent = monthly_income * SECTION_8_RENT_PCT
    subsidy = FAIR_MARKET_RENT_2BR - tenant_rent
    return max(subsidy, 0.0)


def calc_liheap(annual_income: float, profile: BenefitsProfile) -> float:
    """LIHEAP: 150% FPL, seasonal (~$75/month average)."""
    hs = min(profile.household_size, 8)
    fpl = FPL_2026[hs]
    if annual_income > fpl * LIHEAP_FPL_LIMIT_PCT:
        return 0.0
    return LIHEAP_AVG_MONTHLY


# Dispatch map: program name -> calculator function
PROGRAM_CALCULATORS = {
    "SNAP": calc_snap,
    "TANF": calc_tanf,
    "Medicaid": calc_medicaid,
    "ALL_Kids": calc_all_kids,
    "Childcare_Subsidy": calc_childcare,
    "Section_8": calc_section_8,
    "LIHEAP": calc_liheap,
}


def sum_program_benefits(annual_income: float, profile: BenefitsProfile) -> float:
    """Sum all enrolled program benefits at a given annual income.

    Shared implementation used by both cliff_calculator and pvs_scorer.
    Unknown program names are silently skipped.
    """
    return sum(
        calc(annual_income, profile)
        for prog in profile.enrolled_programs
        if (calc := PROGRAM_CALCULATORS.get(prog))
    )
