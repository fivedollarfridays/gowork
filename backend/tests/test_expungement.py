"""Tests for Alabama expungement eligibility check — T26.4."""

import pytest

from app.modules.criminal.expungement import (
    ExpungementEligibility,
    ExpungementResult,
    check_expungement_eligibility,
)
from app.modules.criminal.record_profile import (
    ChargeCategory,
    RecordProfile,
    RecordType,
)


class TestExpungementEligibility:
    """Test check_expungement_eligibility() for all paths."""

    def test_no_record_returns_unknown(self):
        """No record data → UNKNOWN."""
        result = check_expungement_eligibility(None)
        assert result.eligibility == ExpungementEligibility.UNKNOWN

    def test_empty_record_types_unknown(self):
        """Empty record_types → UNKNOWN."""
        profile = RecordProfile()
        result = check_expungement_eligibility(profile)
        assert result.eligibility == ExpungementEligibility.UNKNOWN

    def test_already_expunged(self):
        """Already expunged records → ELIGIBLE_NOW."""
        profile = RecordProfile(record_types=[RecordType.EXPUNGED])
        result = check_expungement_eligibility(profile)
        assert result.eligibility == ExpungementEligibility.ELIGIBLE_NOW

    def test_arrest_only_eligible_now(self):
        """Arrest-only records → ELIGIBLE_NOW (immediate)."""
        profile = RecordProfile(record_types=[RecordType.ARREST_ONLY])
        result = check_expungement_eligibility(profile)
        assert result.eligibility == ExpungementEligibility.ELIGIBLE_NOW
        assert result.years_remaining == 0

    def test_sex_offense_not_eligible(self):
        """Sex offense charges → NOT_ELIGIBLE."""
        profile = RecordProfile(
            record_types=[RecordType.FELONY],
            charge_categories=[ChargeCategory.SEX_OFFENSE],
            years_since_conviction=20,
            completed_sentence=True,
        )
        result = check_expungement_eligibility(profile)
        assert result.eligibility == ExpungementEligibility.NOT_ELIGIBLE

    def test_violent_felony_not_eligible(self):
        """Violence + felony → NOT_ELIGIBLE."""
        profile = RecordProfile(
            record_types=[RecordType.FELONY],
            charge_categories=[ChargeCategory.VIOLENCE],
            years_since_conviction=20,
            completed_sentence=True,
        )
        result = check_expungement_eligibility(profile)
        assert result.eligibility == ExpungementEligibility.NOT_ELIGIBLE

    def test_misdemeanor_3_plus_years_eligible(self):
        """Misdemeanor 3+ years, sentence complete → ELIGIBLE_NOW."""
        profile = RecordProfile(
            record_types=[RecordType.MISDEMEANOR],
            charge_categories=[ChargeCategory.THEFT],
            years_since_conviction=5,
            completed_sentence=True,
        )
        result = check_expungement_eligibility(profile)
        assert result.eligibility == ExpungementEligibility.ELIGIBLE_NOW
        assert result.years_remaining == 0

    def test_misdemeanor_under_3_years_future(self):
        """Misdemeanor <3 years → ELIGIBLE_FUTURE."""
        profile = RecordProfile(
            record_types=[RecordType.MISDEMEANOR],
            charge_categories=[ChargeCategory.THEFT],
            years_since_conviction=1,
            completed_sentence=True,
        )
        result = check_expungement_eligibility(profile)
        assert result.eligibility == ExpungementEligibility.ELIGIBLE_FUTURE
        assert result.years_remaining == 2

    def test_felony_5_plus_years_eligible(self):
        """Nonviolent felony 5+ years, sentence complete → ELIGIBLE_NOW."""
        profile = RecordProfile(
            record_types=[RecordType.FELONY],
            charge_categories=[ChargeCategory.DRUG],
            years_since_conviction=7,
            completed_sentence=True,
        )
        result = check_expungement_eligibility(profile)
        assert result.eligibility == ExpungementEligibility.ELIGIBLE_NOW
        assert result.years_remaining == 0

    def test_felony_under_5_years_future(self):
        """Nonviolent felony <5 years → ELIGIBLE_FUTURE."""
        profile = RecordProfile(
            record_types=[RecordType.FELONY],
            charge_categories=[ChargeCategory.DRUG],
            years_since_conviction=2,
            completed_sentence=True,
        )
        result = check_expungement_eligibility(profile)
        assert result.eligibility == ExpungementEligibility.ELIGIBLE_FUTURE
        assert result.years_remaining == 3

    def test_sentence_not_complete_future(self):
        """Even if years met, incomplete sentence → ELIGIBLE_FUTURE."""
        profile = RecordProfile(
            record_types=[RecordType.MISDEMEANOR],
            charge_categories=[ChargeCategory.THEFT],
            years_since_conviction=10,
            completed_sentence=False,
        )
        result = check_expungement_eligibility(profile)
        assert result.eligibility == ExpungementEligibility.ELIGIBLE_FUTURE

    def test_result_has_steps(self):
        """Result should include actionable steps."""
        profile = RecordProfile(
            record_types=[RecordType.MISDEMEANOR],
            charge_categories=[ChargeCategory.THEFT],
            years_since_conviction=5,
            completed_sentence=True,
        )
        result = check_expungement_eligibility(profile)
        assert len(result.steps) > 0

    def test_result_has_filing_fee(self):
        """Eligible results should mention filing fee."""
        profile = RecordProfile(
            record_types=[RecordType.MISDEMEANOR],
            charge_categories=[ChargeCategory.THEFT],
            years_since_conviction=5,
            completed_sentence=True,
        )
        result = check_expungement_eligibility(profile)
        assert result.filing_fee == "$300"

    def test_not_eligible_has_notes(self):
        """Not eligible result should have explanatory notes."""
        profile = RecordProfile(
            record_types=[RecordType.FELONY],
            charge_categories=[ChargeCategory.SEX_OFFENSE],
        )
        result = check_expungement_eligibility(profile)
        assert result.notes is not None
        assert len(result.notes) > 0

    def test_no_years_data_future(self):
        """Misdemeanor with no years_since_conviction → ELIGIBLE_FUTURE."""
        profile = RecordProfile(
            record_types=[RecordType.MISDEMEANOR],
            charge_categories=[ChargeCategory.THEFT],
            completed_sentence=True,
        )
        result = check_expungement_eligibility(profile)
        assert result.eligibility == ExpungementEligibility.ELIGIBLE_FUTURE
