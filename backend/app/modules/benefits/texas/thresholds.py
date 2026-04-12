"""Texas-specific benefit program thresholds and constants (2026 estimated).

Sources:
- FPL: Federal, same nationwide (HHS 2026 guidelines)
- SNAP: Federal maximums (USDA FNS FY2026)
- TANF: Texas HHSC (higher than Alabama)
- CHIP: Texas HHSC — 200% FPL (Children's Health Insurance Program)
- SMI: Census Bureau / HHS — Texas values
- AMI: HUD — Fort Worth-Arlington MSA
- Childcare: TWC / Child Care Aware of America — Fort Worth average
- FMR: HUD — Fort Worth-Arlington MSA 2-bedroom
- CEAP: TX CEAP (Comprehensive Energy Assistance Program) replaces LIHEAP
"""

# Shared time-conversion constants (same as Alabama module)
HOURS_PER_YEAR = 2080
MONTHS_PER_YEAR = 12

# Federal Poverty Level 2026 by household size (federal — same in all states)
FPL_2026: dict[int, float] = {
    1: 15_600, 2: 21_200, 3: 26_700, 4: 32_300,
    5: 37_900, 6: 43_500, 7: 49_100, 8: 54_700,
}

# SNAP maximum monthly benefit by household size (federal — same in all states)
SNAP_MAX_BENEFIT: dict[int, float] = {
    1: 291, 2: 535, 3: 766, 4: 973,
    5: 1_155, 6: 1_386, 7: 1_532, 8: 1_751,
}

# SNAP: 30% of net income deducted from max benefit (federal)
SNAP_INCOME_DEDUCTION_RATE = 0.30

# SNAP standard deduction by household size (federal)
SNAP_STANDARD_DEDUCTION: dict[int, float] = {
    1: 198, 2: 198, 3: 198, 4: 208, 5: 244, 6: 279, 7: 279, 8: 279,
}

# TANF — Texas has higher benefits than Alabama
# Source: Texas HHSC TANF payment standards
TANF_MAX_MONTHLY: dict[int, float] = {
    1: 184, 2: 236, 3: 308, 4: 380, 5: 431, 6: 482, 7: 533, 8: 584,
}

# CHIP (Children's Health Insurance Program) — replaces Alabama's ALL Kids
# Texas CHIP income limit: 200% FPL
CHIP_FPL_PCT = 2.00
# Estimated monthly Medicaid/CHIP value per child
MEDICAID_CHILD_VALUE = 375.0

# Childcare subsidy — 85% of State Median Income (Texas SMI 2026 est.)
# Source: Census Bureau / TWC
SMI_2026: dict[int, float] = {
    1: 40_200, 2: 52_600, 3: 65_000, 4: 77_400,
    5: 89_800, 6: 102_200, 7: 105_000, 8: 107_800,
}
CHILDCARE_SMI_LIMIT_PCT = 0.85

# Average monthly childcare cost in Fort Worth (per child under 6)
# Source: Child Care Aware of America / TWC
CHILDCARE_MONTHLY_COST = 1_100.0

# Copay percentage tiers: (income_as_pct_of_smi, copay_pct_of_cost)
CHILDCARE_COPAY_TIERS: list[tuple[float, float]] = [
    (0.25, 0.02), (0.40, 0.05), (0.55, 0.08),
    (0.70, 0.12), (0.85, 0.20),
]

# Section 8 Housing — 50% of Area Median Income (Fort Worth-Arlington MSA)
# Source: HUD FY2026 Income Limits
AMI_FORT_WORTH_2026: dict[int, float] = {
    1: 54_600, 2: 62_400, 3: 70_200, 4: 78_000,
    5: 84_200, 6: 90_500, 7: 96_700, 8: 103_000,
}
SECTION_8_AMI_LIMIT_PCT = 0.50
SECTION_8_RENT_PCT = 0.30

# Fair market rent 2-bedroom Fort Worth (HUD 2026 est.)
FAIR_MARKET_RENT_2BR = 1_350.0

# CEAP (Comprehensive Energy Assistance Program) — Texas equivalent of LIHEAP
# Source: TX TDHCA (Texas Dept of Housing and Community Affairs)
CEAP_FPL_LIMIT_PCT = 1.50
CEAP_AVG_MONTHLY = 85.0

# Tax rates (simplified — same federal rates)
FICA_RATE = 0.0765
TAX_BRACKETS: list[tuple[float, float]] = [
    (11_600, 0.0),
    (23_200, 0.10),
    (52_800, 0.12),
    (100_000, 0.22),
]
