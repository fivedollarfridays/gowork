"""Tests for benefits string enums — CliffSeverity and CliffType."""

from enum import Enum


class TestCliffSeverityEnum:
    """CliffSeverity is a str enum with values mild, moderate, severe."""

    def test_enum_exists(self):
        from app.modules.benefits.types import CliffSeverity

        assert issubclass(CliffSeverity, str)
        assert issubclass(CliffSeverity, Enum)

    def test_enum_values(self):
        from app.modules.benefits.types import CliffSeverity

        assert CliffSeverity.MILD == "mild"
        assert CliffSeverity.MODERATE == "moderate"
        assert CliffSeverity.SEVERE == "severe"

    def test_enum_members_count(self):
        from app.modules.benefits.types import CliffSeverity

        assert len(CliffSeverity) == 3

    def test_str_equality(self):
        """str enums compare equal to their string values."""
        from app.modules.benefits.types import CliffSeverity

        assert CliffSeverity.MILD == "mild"
        assert "moderate" == CliffSeverity.MODERATE
        assert CliffSeverity.SEVERE in ("mild", "moderate", "severe")


class TestCliffTypeEnum:
    """CliffType is a str enum with values gradual, hard."""

    def test_enum_exists(self):
        from app.modules.benefits.types import CliffType

        assert issubclass(CliffType, str)
        assert issubclass(CliffType, Enum)

    def test_enum_values(self):
        from app.modules.benefits.types import CliffType

        assert CliffType.GRADUAL == "gradual"
        assert CliffType.HARD == "hard"

    def test_enum_members_count(self):
        from app.modules.benefits.types import CliffType

        assert len(CliffType) == 2


class TestCliffPointUsesEnum:
    """CliffPoint.severity field should be typed as CliffSeverity."""

    def test_severity_field_is_enum(self):
        from app.modules.benefits.types import CliffPoint, CliffSeverity

        point = CliffPoint(
            hourly_wage=15.0,
            annual_income=31200.0,
            net_monthly_income=2400.0,
            lost_program="SNAP",
            monthly_loss=100.0,
            severity=CliffSeverity.MODERATE,
        )
        assert isinstance(point.severity, CliffSeverity)

    def test_severity_field_accepts_string(self):
        """Pydantic should coerce string to enum."""
        from app.modules.benefits.types import CliffPoint, CliffSeverity

        point = CliffPoint(
            hourly_wage=15.0,
            annual_income=31200.0,
            net_monthly_income=2400.0,
            lost_program="SNAP",
            monthly_loss=100.0,
            severity="moderate",
        )
        assert isinstance(point.severity, CliffSeverity)
        assert point.severity == CliffSeverity.MODERATE


class TestProgramBenefitUsesEnum:
    """ProgramBenefit.cliff_type field should be typed as CliffType."""

    def test_cliff_type_field_is_enum(self):
        from app.modules.benefits.types import CliffType, ProgramBenefit

        prog = ProgramBenefit(
            program="SNAP",
            monthly_value=200.0,
            eligible=True,
            phase_out_start=10000.0,
            phase_out_end=20000.0,
            cliff_type=CliffType.GRADUAL,
        )
        assert isinstance(prog.cliff_type, CliffType)

    def test_cliff_type_field_accepts_string(self):
        """Pydantic should coerce string to enum."""
        from app.modules.benefits.types import CliffType, ProgramBenefit

        prog = ProgramBenefit(
            program="SNAP",
            monthly_value=200.0,
            eligible=True,
            phase_out_start=10000.0,
            phase_out_end=20000.0,
            cliff_type="gradual",
        )
        assert isinstance(prog.cliff_type, CliffType)
        assert prog.cliff_type == CliffType.GRADUAL


class TestCliffCalculatorReturnsEnum:
    """classify_cliff_severity should return CliffSeverity enum values."""

    def test_classify_returns_enum(self):
        from app.modules.benefits.cliff_calculator import classify_cliff_severity
        from app.modules.benefits.types import CliffSeverity

        result = classify_cliff_severity(100.0)
        assert isinstance(result, CliffSeverity)

    def test_classify_mild_returns_enum(self):
        from app.modules.benefits.cliff_calculator import classify_cliff_severity
        from app.modules.benefits.types import CliffSeverity

        assert classify_cliff_severity(30.0) is CliffSeverity.MILD

    def test_classify_moderate_returns_enum(self):
        from app.modules.benefits.cliff_calculator import classify_cliff_severity
        from app.modules.benefits.types import CliffSeverity

        assert classify_cliff_severity(100.0) is CliffSeverity.MODERATE

    def test_classify_severe_returns_enum(self):
        from app.modules.benefits.cliff_calculator import classify_cliff_severity
        from app.modules.benefits.types import CliffSeverity

        assert classify_cliff_severity(250.0) is CliffSeverity.SEVERE


class TestCliffImpactUsesEnum:
    """CliffImpact.severity in matching/types.py should use CliffSeverity."""

    def test_cliff_impact_severity_is_enum(self):
        from app.modules.benefits.types import CliffSeverity
        from app.modules.matching.types import CliffImpact

        impact = CliffImpact(
            benefits_change=-150.0,
            net_monthly_change=-100.0,
            has_cliff=True,
            severity=CliffSeverity.MODERATE,
            affected_programs=["SNAP"],
        )
        assert isinstance(impact.severity, CliffSeverity)

    def test_cliff_impact_severity_accepts_string(self):
        """Pydantic should coerce string to CliffSeverity."""
        from app.modules.benefits.types import CliffSeverity
        from app.modules.matching.types import CliffImpact

        impact = CliffImpact(
            benefits_change=-150.0,
            net_monthly_change=-100.0,
            has_cliff=True,
            severity="moderate",
            affected_programs=["SNAP"],
        )
        assert isinstance(impact.severity, CliffSeverity)

    def test_cliff_impact_severity_none_allowed(self):
        from app.modules.matching.types import CliffImpact

        impact = CliffImpact(
            benefits_change=0.0,
            net_monthly_change=50.0,
            has_cliff=False,
            severity=None,
            affected_programs=[],
        )
        assert impact.severity is None
