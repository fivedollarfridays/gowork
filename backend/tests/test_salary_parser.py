"""Tests for salary extraction and earnings scoring."""

from app.modules.matching.salary_parser import SalaryInfo, extract_salary, score_earnings


class TestExtractSalaryEdgeCases:
    """Cycle 1: edge cases return None gracefully."""

    def test_none_input_returns_none(self) -> None:
        assert extract_salary(None) is None

    def test_empty_string_returns_none(self) -> None:
        assert extract_salary("") is None

    def test_no_pay_info_returns_none(self) -> None:
        assert extract_salary("Great benefits and team culture!") is None


class TestExtractSingleHourly:
    """Cycle 2: single hourly rate parsing."""

    def test_dollar_per_hr(self) -> None:
        result = extract_salary("$15/hr")
        assert result is not None
        assert result.hourly_rate == 15.0
        assert result.annual_estimate == 31200.0
        assert result.is_range is False

    def test_dollar_per_hour(self) -> None:
        result = extract_salary("pay: $18.50 per hour")
        assert result is not None
        assert result.hourly_rate == 18.50
        assert result.annual_estimate == 38480.0
        assert result.is_range is False

    def test_dollar_an_hour(self) -> None:
        result = extract_salary("$12.00 an hour")
        assert result is not None
        assert result.hourly_rate == 12.0
        assert result.annual_estimate == 24960.0
        assert result.is_range is False


class TestExtractHourlyRange:
    """Cycle 3: hourly range parsing (midpoint)."""

    def test_range_to_per_hour(self) -> None:
        result = extract_salary("starting pay range of $12.00 to $12.50 per hour")
        assert result is not None
        assert result.hourly_rate == 12.25
        assert result.annual_estimate == 25480.0
        assert result.is_range is True

    def test_range_dash_per_hour(self) -> None:
        result = extract_salary("$15.50 - $20.00 per hour")
        assert result is not None
        assert result.hourly_rate == 17.75
        assert result.annual_estimate == 36920.0
        assert result.is_range is True


class TestExtractAnnualSalary:
    """Cycle 4: annual salary parsing."""

    def test_implausible_annual_salary_rejected(self) -> None:
        """Annual amount below $5,000 minimum -> returns None."""
        result = extract_salary("$45 per year warehouse job")
        assert result is None

    def test_annual_with_comma(self) -> None:
        result = extract_salary("salary $45,000 per year")
        assert result is not None
        assert result.annual_estimate == 45000.0
        assert abs(result.hourly_rate - 21.63) < 0.01
        assert result.is_range is False

    def test_annual_with_k_suffix(self) -> None:
        result = extract_salary("$45K per year")
        assert result is not None
        assert result.annual_estimate == 45000.0
        assert abs(result.hourly_rate - 21.63) < 0.01
        assert result.is_range is False

    def test_annual_with_k_slash_year(self) -> None:
        result = extract_salary("$45k/year")
        assert result is not None
        assert result.annual_estimate == 45000.0
        assert abs(result.hourly_rate - 21.63) < 0.01
        assert result.is_range is False


class TestExtractFromRealDescription:
    """Cycle 5: salary extraction from realistic Indeed-style descriptions."""

    def test_indeed_description_with_range(self) -> None:
        description = (
            "We are hiring a Warehouse Associate to join our team in "
            "Montgomery, AL. Responsibilities include loading/unloading, "
            "inventory management, and forklift operation. Must be able to "
            "lift 50 lbs. Full-time position with benefits after 90 days. "
            "Starting pay range of $12.00 to $12.50 per hour depending on "
            "experience. Apply online or in person at our facility."
        )
        result = extract_salary(description)
        assert result is not None
        assert result.hourly_rate == 12.25
        assert result.annual_estimate == 25480.0
        assert result.is_range is True


class TestScoreEarnings:
    """Cycle 6: earnings scoring function."""

    def test_none_salary_returns_penalty(self) -> None:
        assert score_earnings(None) == 0.05

    def test_low_hourly_floors_at_minimum(self) -> None:
        """$7.25/hr = $15,080/year -> 15080/40000 = 0.377, above floor 0.15."""
        salary = SalaryInfo(
            hourly_rate=7.25, annual_estimate=15080.0,
            is_range=False, raw_text="$7.25/hr",
        )
        result = score_earnings(salary)
        assert result >= 0.15
        assert abs(result - 0.377) < 0.001

    def test_midrange_hourly(self) -> None:
        """$12.25/hr = $25,480/year -> 25480/40000 = 0.637."""
        salary = SalaryInfo(
            hourly_rate=12.25, annual_estimate=25480.0,
            is_range=True, raw_text="$12.00 to $12.50 per hour",
        )
        result = score_earnings(salary)
        assert abs(result - 0.637) < 0.001

    def test_high_annual_caps_at_one(self) -> None:
        """$50,000/year -> 50000/40000 = 1.25, capped at 1.0."""
        salary = SalaryInfo(
            hourly_rate=24.04, annual_estimate=50000.0,
            is_range=False, raw_text="$50,000 per year",
        )
        assert score_earnings(salary) == 1.0
