"""Alabama-specific benefit program thresholds and constants (2026 estimated)."""

# Shared time-conversion constants
HOURS_PER_YEAR = 2080
MONTHS_PER_YEAR = 12

# Federal Poverty Level 2026 by household size
FPL_2026: dict[int, float] = {
    1: 15_600,
    2: 21_200,
    3: 26_700,
    4: 32_300,
    5: 37_900,
    6: 43_500,
    7: 49_100,
    8: 54_700,
}

# SNAP maximum monthly benefit by household size (FY2026 estimated)
SNAP_MAX_BENEFIT: dict[int, float] = {
    1: 291,
    2: 535,
    3: 766,
    4: 973,
    5: 1_155,
    6: 1_386,
    7: 1_532,
    8: 1_751,
}

# SNAP: 30% of net income deducted from max benefit
SNAP_INCOME_DEDUCTION_RATE = 0.30
# SNAP standard deduction by household size (1-3: $198, 4: $208, 5: $244, 6+: $279)
SNAP_STANDARD_DEDUCTION: dict[int, float] = {
    1: 198, 2: 198, 3: 198, 4: 208, 5: 244, 6: 279, 7: 279, 8: 279,
}

# TANF — Alabama has extremely low benefits
TANF_MAX_MONTHLY: dict[int, float] = {
    1: 147, 2: 175, 3: 215, 4: 246, 5: 268, 6: 290, 7: 312, 8: 334,
}

# ALL Kids (Medicaid for children) — 317% FPL
ALL_KIDS_FPL_PCT = 3.17
# Estimated monthly Medicaid value per child
MEDICAID_CHILD_VALUE = 350.0

# Childcare subsidy — 85% of State Median Income (Alabama SMI 2026 est.)
SMI_2026: dict[int, float] = {
    1: 35_000, 2: 45_800, 3: 56_600, 4: 67_400,
    5: 78_200, 6: 89_000, 7: 91_500, 8: 94_000,
}
CHILDCARE_SMI_LIMIT_PCT = 0.85
# Average monthly childcare cost in Montgomery (per child under 6)
CHILDCARE_MONTHLY_COST = 850.0
# Copay percentage tiers: (income_as_pct_of_smi, copay_pct_of_cost)
CHILDCARE_COPAY_TIERS: list[tuple[float, float]] = [
    (0.25, 0.02), (0.40, 0.05), (0.55, 0.08),
    (0.70, 0.12), (0.85, 0.20),
]

# Section 8 Housing — 50% of Area Median Income (Montgomery MSA)
AMI_MONTGOMERY_2026: dict[int, float] = {
    1: 42_000, 2: 48_000, 3: 54_000, 4: 60_000,
    5: 64_800, 6: 69_600, 7: 74_400, 8: 79_200,
}
SECTION_8_AMI_LIMIT_PCT = 0.50
# Rent is 30% of income; subsidy covers the rest
SECTION_8_RENT_PCT = 0.30
# Fair market rent 2-bedroom Montgomery (HUD 2026 est.)
FAIR_MARKET_RENT_2BR = 950.0

# LIHEAP — 150% FPL, seasonal
LIHEAP_FPL_LIMIT_PCT = 1.50
LIHEAP_AVG_MONTHLY = 75.0

# Tax rates (simplified)
FICA_RATE = 0.0765
# Simplified effective income tax rate by annual bracket
TAX_BRACKETS: list[tuple[float, float]] = [
    (11_600, 0.0),    # standard deduction — no tax
    (23_200, 0.10),   # 10% bracket
    (52_800, 0.12),   # 12% bracket
    (100_000, 0.22),  # 22% bracket (well above our $25/hr range)
]
