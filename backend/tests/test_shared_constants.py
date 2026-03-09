"""Tests for shared constants in thresholds module."""


def test_hours_per_year_importable_from_thresholds():
    """HOURS_PER_YEAR should be importable from thresholds and equal 2080."""
    from app.modules.benefits.thresholds import HOURS_PER_YEAR

    assert HOURS_PER_YEAR == 2080


def test_months_per_year_importable_from_thresholds():
    """MONTHS_PER_YEAR should be importable from thresholds and equal 12."""
    from app.modules.benefits.thresholds import MONTHS_PER_YEAR

    assert MONTHS_PER_YEAR == 12


def test_cliff_calculator_uses_thresholds_hours():
    """cliff_calculator.HOURS_PER_YEAR should come from thresholds."""
    from app.modules.benefits import cliff_calculator, thresholds

    assert cliff_calculator.HOURS_PER_YEAR is thresholds.HOURS_PER_YEAR


def test_cliff_calculator_uses_thresholds_months():
    """cliff_calculator.MONTHS_PER_YEAR should come from thresholds."""
    from app.modules.benefits import cliff_calculator, thresholds

    assert cliff_calculator.MONTHS_PER_YEAR is thresholds.MONTHS_PER_YEAR


def test_program_calculators_uses_thresholds_months():
    """program_calculators.MONTHS_PER_YEAR should come from thresholds."""
    from app.modules.benefits import program_calculators, thresholds

    assert program_calculators.MONTHS_PER_YEAR is thresholds.MONTHS_PER_YEAR


def test_pvs_scorer_uses_thresholds_hours():
    """pvs_scorer.HOURS_PER_YEAR should come from thresholds."""
    from app.modules.benefits import thresholds
    from app.modules.matching import pvs_scorer

    assert pvs_scorer.HOURS_PER_YEAR is thresholds.HOURS_PER_YEAR


def test_pvs_scorer_uses_thresholds_months():
    """pvs_scorer.MONTHS_PER_YEAR should come from thresholds."""
    from app.modules.benefits import thresholds
    from app.modules.matching import pvs_scorer

    assert pvs_scorer.MONTHS_PER_YEAR is thresholds.MONTHS_PER_YEAR


def test_salary_parser_uses_thresholds_hours():
    """salary_parser.HOURS_PER_YEAR should come from thresholds."""
    from app.modules.benefits import thresholds
    from app.modules.matching import salary_parser

    assert salary_parser.HOURS_PER_YEAR is thresholds.HOURS_PER_YEAR


def test_brightdata_cache_uses_thresholds_hours():
    """brightdata cache._HOURS_PER_YEAR should come from thresholds."""
    from app.integrations.brightdata import cache
    from app.modules.benefits import thresholds

    assert cache._HOURS_PER_YEAR is thresholds.HOURS_PER_YEAR
