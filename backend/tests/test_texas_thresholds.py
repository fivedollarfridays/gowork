"""Tests for Texas-specific benefit program thresholds."""

import pytest


def test_fpl_2026_has_all_household_sizes():
    """FPL values must exist for household sizes 1-8."""
    from app.modules.benefits.texas.thresholds import FPL_2026

    for size in range(1, 9):
        assert size in FPL_2026
        assert FPL_2026[size] > 0


def test_fpl_2026_is_federal_same_as_alabama():
    """FPL is a federal value -- same in both states."""
    from app.modules.benefits.texas.thresholds import FPL_2026
    from app.modules.benefits.thresholds import FPL_2026 as AL_FPL

    for size in range(1, 9):
        assert FPL_2026[size] == AL_FPL[size]


def test_snap_max_benefit_federal():
    """SNAP max benefit is federal -- same in both states."""
    from app.modules.benefits.texas.thresholds import SNAP_MAX_BENEFIT
    from app.modules.benefits.thresholds import SNAP_MAX_BENEFIT as AL_SNAP

    for size in range(1, 9):
        assert SNAP_MAX_BENEFIT[size] == AL_SNAP[size]


def test_tanf_higher_than_alabama():
    """Texas TANF benefits are higher than Alabama's extremely low benefits."""
    from app.modules.benefits.texas.thresholds import TANF_MAX_MONTHLY
    from app.modules.benefits.thresholds import TANF_MAX_MONTHLY as AL_TANF

    for size in range(1, 9):
        assert TANF_MAX_MONTHLY[size] > AL_TANF[size]


def test_chip_replaces_all_kids():
    """Texas uses CHIP instead of ALL Kids -- 200% FPL."""
    from app.modules.benefits.texas.thresholds import CHIP_FPL_PCT

    assert CHIP_FPL_PCT == pytest.approx(2.00)


def test_smi_texas_higher_than_alabama():
    """Texas State Median Income is higher than Alabama's."""
    from app.modules.benefits.texas.thresholds import SMI_2026
    from app.modules.benefits.thresholds import SMI_2026 as AL_SMI

    for size in range(1, 9):
        assert SMI_2026[size] > AL_SMI[size]


def test_ami_fort_worth_higher_than_montgomery():
    """Fort Worth AMI is significantly higher than Montgomery AMI."""
    from app.modules.benefits.texas.thresholds import AMI_FORT_WORTH_2026
    from app.modules.benefits.thresholds import AMI_MONTGOMERY_2026

    for size in range(1, 9):
        assert AMI_FORT_WORTH_2026[size] > AMI_MONTGOMERY_2026[size]


def test_childcare_cost_higher_in_fort_worth():
    """Fort Worth childcare costs more than Montgomery."""
    from app.modules.benefits.texas.thresholds import CHILDCARE_MONTHLY_COST
    from app.modules.benefits.thresholds import CHILDCARE_MONTHLY_COST as AL_COST

    assert CHILDCARE_MONTHLY_COST > AL_COST


def test_fair_market_rent_higher_in_fort_worth():
    """Fort Worth FMR is higher than Montgomery."""
    from app.modules.benefits.texas.thresholds import FAIR_MARKET_RENT_2BR
    from app.modules.benefits.thresholds import FAIR_MARKET_RENT_2BR as AL_FMR

    assert FAIR_MARKET_RENT_2BR > AL_FMR


def test_ceap_replaces_liheap():
    """Texas uses CEAP instead of LIHEAP."""
    from app.modules.benefits.texas.thresholds import CEAP_FPL_LIMIT_PCT, CEAP_AVG_MONTHLY

    assert CEAP_FPL_LIMIT_PCT == pytest.approx(1.50)
    assert CEAP_AVG_MONTHLY > 0


def test_all_threshold_dicts_have_8_entries():
    """All household-size dicts must have entries for sizes 1-8."""
    from app.modules.benefits.texas.thresholds import (
        FPL_2026, SNAP_MAX_BENEFIT, SNAP_STANDARD_DEDUCTION,
        TANF_MAX_MONTHLY, SMI_2026, AMI_FORT_WORTH_2026,
    )

    for name, d in [
        ("FPL_2026", FPL_2026), ("SNAP_MAX_BENEFIT", SNAP_MAX_BENEFIT),
        ("SNAP_STANDARD_DEDUCTION", SNAP_STANDARD_DEDUCTION),
        ("TANF_MAX_MONTHLY", TANF_MAX_MONTHLY), ("SMI_2026", SMI_2026),
        ("AMI_FORT_WORTH_2026", AMI_FORT_WORTH_2026),
    ]:
        for size in range(1, 9):
            assert size in d, f"{name} missing size {size}"
