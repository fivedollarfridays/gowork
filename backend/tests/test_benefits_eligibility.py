"""Tests for benefits program eligibility screener."""

from app.modules.benefits.eligibility_screener import screen_benefits_eligibility
from app.modules.benefits.thresholds import (
    AMI_MONTGOMERY_2026,
    FPL_2026,
    MONTHS_PER_YEAR,
    SMI_2026,
)
from app.modules.benefits.types import (
    BenefitsProfile,
    EligibilityConfidence,
)


def _profile(**overrides) -> BenefitsProfile:
    defaults = {
        "household_size": 3,
        "current_monthly_income": 0,
        "enrolled_programs": [],
        "dependents_under_6": 0,
        "dependents_6_to_17": 0,
    }
    defaults.update(overrides)
    return BenefitsProfile(**defaults)


# ---------------------------------------------------------------------------
# Basic structure
# ---------------------------------------------------------------------------

class TestScreenerStructure:
    def test_returns_all_seven_programs(self):
        result = screen_benefits_eligibility(_profile())
        all_programs = result.eligible_programs + result.ineligible_programs
        names = {p.program for p in all_programs}
        assert names == {
            "SNAP", "TANF", "Medicaid", "ALL_Kids",
            "Childcare_Subsidy", "Section_8", "LIHEAP",
        }

    def test_disclaimer_present(self):
        result = screen_benefits_eligibility(_profile())
        assert result.disclaimer
        assert "estimate" in result.disclaimer.lower() or "DHR" in result.disclaimer

    def test_total_estimated_monthly_sums_eligible(self):
        result = screen_benefits_eligibility(_profile())
        expected = sum(p.estimated_monthly_value for p in result.eligible_programs)
        assert result.total_estimated_monthly == round(expected, 2)


# ---------------------------------------------------------------------------
# SNAP eligibility
# ---------------------------------------------------------------------------

class TestSnapEligibility:
    def test_eligible_at_zero_income(self):
        result = screen_benefits_eligibility(_profile(current_monthly_income=0))
        snap = _find_program(result, "SNAP")
        assert snap.eligible is True

    def test_eligible_below_130_fpl(self):
        fpl_3 = FPL_2026[3]
        monthly = (fpl_3 * 1.20) / MONTHS_PER_YEAR  # 120% FPL, below 130%
        result = screen_benefits_eligibility(_profile(current_monthly_income=monthly))
        snap = _find_program(result, "SNAP")
        assert snap.eligible is True

    def test_ineligible_above_130_fpl(self):
        fpl_3 = FPL_2026[3]
        monthly = (fpl_3 * 1.40) / MONTHS_PER_YEAR  # 140% FPL
        result = screen_benefits_eligibility(_profile(current_monthly_income=monthly))
        snap = _find_program(result, "SNAP")
        assert snap.eligible is False

    def test_has_positive_monthly_value(self):
        result = screen_benefits_eligibility(_profile())
        snap = _find_program(result, "SNAP")
        assert snap.estimated_monthly_value > 0

    def test_income_headroom_positive_when_eligible(self):
        result = screen_benefits_eligibility(_profile(current_monthly_income=500))
        snap = _find_program(result, "SNAP")
        assert snap.eligible is True
        assert snap.income_headroom > 0

    def test_reason_present(self):
        result = screen_benefits_eligibility(_profile())
        snap = _find_program(result, "SNAP")
        assert snap.reason


# ---------------------------------------------------------------------------
# TANF eligibility
# ---------------------------------------------------------------------------

class TestTanfEligibility:
    def test_eligible_at_low_income(self):
        result = screen_benefits_eligibility(_profile(current_monthly_income=0))
        tanf = _find_program(result, "TANF")
        assert tanf.eligible is True

    def test_ineligible_at_high_income(self):
        result = screen_benefits_eligibility(
            _profile(current_monthly_income=3000),
        )
        tanf = _find_program(result, "TANF")
        assert tanf.eligible is False


# ---------------------------------------------------------------------------
# Medicaid — Alabama no expansion
# ---------------------------------------------------------------------------

class TestMedicaidEligibility:
    def test_always_ineligible_for_adults(self):
        result = screen_benefits_eligibility(_profile(current_monthly_income=0))
        medicaid = _find_program(result, "Medicaid")
        assert medicaid.eligible is False
        assert medicaid.confidence == EligibilityConfidence.UNLIKELY

    def test_reason_mentions_alabama(self):
        result = screen_benefits_eligibility(_profile())
        medicaid = _find_program(result, "Medicaid")
        assert "alabama" in medicaid.reason.lower() or "expansion" in medicaid.reason.lower()


# ---------------------------------------------------------------------------
# ALL_Kids — requires dependents
# ---------------------------------------------------------------------------

class TestAllKidsEligibility:
    def test_eligible_with_children(self):
        result = screen_benefits_eligibility(
            _profile(dependents_6_to_17=2),
        )
        all_kids = _find_program(result, "ALL_Kids")
        assert all_kids.eligible is True

    def test_ineligible_without_children(self):
        result = screen_benefits_eligibility(
            _profile(dependents_under_6=0, dependents_6_to_17=0),
        )
        all_kids = _find_program(result, "ALL_Kids")
        assert all_kids.eligible is False

    def test_ineligible_above_317_fpl(self):
        fpl_3 = FPL_2026[3]
        monthly = (fpl_3 * 3.20) / MONTHS_PER_YEAR
        result = screen_benefits_eligibility(
            _profile(current_monthly_income=monthly, dependents_6_to_17=1),
        )
        all_kids = _find_program(result, "ALL_Kids")
        assert all_kids.eligible is False

    def test_value_scales_with_children(self):
        r1 = screen_benefits_eligibility(_profile(dependents_6_to_17=1))
        r2 = screen_benefits_eligibility(_profile(dependents_6_to_17=2))
        v1 = _find_program(r1, "ALL_Kids").estimated_monthly_value
        v2 = _find_program(r2, "ALL_Kids").estimated_monthly_value
        assert v2 > v1


# ---------------------------------------------------------------------------
# Childcare subsidy — requires under-6 dependents
# ---------------------------------------------------------------------------

class TestChildcareEligibility:
    def test_eligible_with_young_children(self):
        result = screen_benefits_eligibility(
            _profile(dependents_under_6=1),
        )
        cc = _find_program(result, "Childcare_Subsidy")
        assert cc.eligible is True

    def test_ineligible_without_young_children(self):
        result = screen_benefits_eligibility(
            _profile(dependents_under_6=0, dependents_6_to_17=2),
        )
        cc = _find_program(result, "Childcare_Subsidy")
        assert cc.eligible is False

    def test_ineligible_above_85_smi(self):
        smi_3 = SMI_2026[3]
        monthly = (smi_3 * 0.90) / MONTHS_PER_YEAR  # 90% SMI
        result = screen_benefits_eligibility(
            _profile(current_monthly_income=monthly, dependents_under_6=1),
        )
        cc = _find_program(result, "Childcare_Subsidy")
        assert cc.eligible is False


# ---------------------------------------------------------------------------
# Section 8 — waitlist reality
# ---------------------------------------------------------------------------

class TestSection8Eligibility:
    def test_eligible_below_50_ami(self):
        result = screen_benefits_eligibility(_profile(current_monthly_income=0))
        s8 = _find_program(result, "Section_8")
        assert s8.eligible is True

    def test_ineligible_above_50_ami(self):
        ami_3 = AMI_MONTGOMERY_2026[3]
        monthly = (ami_3 * 0.55) / MONTHS_PER_YEAR
        result = screen_benefits_eligibility(
            _profile(current_monthly_income=monthly),
        )
        s8 = _find_program(result, "Section_8")
        assert s8.eligible is False

    def test_reason_mentions_waitlist(self):
        result = screen_benefits_eligibility(_profile())
        s8 = _find_program(result, "Section_8")
        if s8.eligible:
            assert "wait" in s8.reason.lower()


# ---------------------------------------------------------------------------
# LIHEAP — seasonal
# ---------------------------------------------------------------------------

class TestLiheapEligibility:
    def test_eligible_below_150_fpl(self):
        result = screen_benefits_eligibility(_profile(current_monthly_income=0))
        liheap = _find_program(result, "LIHEAP")
        assert liheap.eligible is True

    def test_ineligible_above_150_fpl(self):
        fpl_3 = FPL_2026[3]
        monthly = (fpl_3 * 1.60) / MONTHS_PER_YEAR
        result = screen_benefits_eligibility(
            _profile(current_monthly_income=monthly),
        )
        liheap = _find_program(result, "LIHEAP")
        assert liheap.eligible is False

    def test_reason_mentions_seasonal(self):
        result = screen_benefits_eligibility(_profile())
        liheap = _find_program(result, "LIHEAP")
        if liheap.eligible:
            assert "season" in liheap.reason.lower()


# ---------------------------------------------------------------------------
# Confidence levels
# ---------------------------------------------------------------------------

class TestConfidence:
    def test_likely_when_well_below_threshold(self):
        result = screen_benefits_eligibility(_profile(current_monthly_income=0))
        snap = _find_program(result, "SNAP")
        assert snap.eligible is True
        assert snap.confidence == EligibilityConfidence.LIKELY

    def test_possible_near_threshold(self):
        """Income within 10% of SNAP 130% FPL threshold → possible."""
        fpl_3 = FPL_2026[3]
        threshold = fpl_3 * 1.30
        # 93% of threshold — within 10% band
        monthly = (threshold * 0.93) / MONTHS_PER_YEAR
        result = screen_benefits_eligibility(
            _profile(current_monthly_income=monthly),
        )
        snap = _find_program(result, "SNAP")
        assert snap.eligible is True
        assert snap.confidence == EligibilityConfidence.POSSIBLE

    def test_unlikely_when_ineligible(self):
        fpl_3 = FPL_2026[3]
        monthly = (fpl_3 * 2.0) / MONTHS_PER_YEAR
        result = screen_benefits_eligibility(
            _profile(current_monthly_income=monthly),
        )
        snap = _find_program(result, "SNAP")
        assert snap.eligible is False
        assert snap.confidence == EligibilityConfidence.UNLIKELY


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_zero_income_maximum_eligibility(self):
        """Zero income should qualify for most programs."""
        result = screen_benefits_eligibility(
            _profile(current_monthly_income=0, dependents_under_6=1, dependents_6_to_17=1),
        )
        eligible_names = {p.program for p in result.eligible_programs}
        # All except Medicaid adults
        assert "SNAP" in eligible_names
        assert "TANF" in eligible_names
        assert "ALL_Kids" in eligible_names
        assert "Childcare_Subsidy" in eligible_names
        assert "Section_8" in eligible_names
        assert "LIHEAP" in eligible_names
        assert "Medicaid" not in eligible_names

    def test_household_size_1(self):
        result = screen_benefits_eligibility(
            _profile(household_size=1, current_monthly_income=0),
        )
        snap = _find_program(result, "SNAP")
        assert snap.eligible is True

    def test_household_size_8(self):
        result = screen_benefits_eligibility(
            _profile(household_size=8, current_monthly_income=0),
        )
        snap = _find_program(result, "SNAP")
        assert snap.eligible is True

    def test_income_headroom_zero_when_ineligible(self):
        fpl_3 = FPL_2026[3]
        monthly = (fpl_3 * 2.0) / MONTHS_PER_YEAR
        result = screen_benefits_eligibility(
            _profile(current_monthly_income=monthly),
        )
        snap = _find_program(result, "SNAP")
        assert snap.income_headroom <= 0

    def test_no_duplicate_programs(self):
        result = screen_benefits_eligibility(_profile())
        all_names = [p.program for p in result.eligible_programs + result.ineligible_programs]
        assert len(all_names) == len(set(all_names))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_program(result, name: str):
    """Find a program in eligible or ineligible lists."""
    for p in result.eligible_programs + result.ineligible_programs:
        if p.program == name:
            return p
    raise ValueError(f"Program {name} not found in result")
