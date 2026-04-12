"""Tests for Texas expunction and nondisclosure eligibility."""

import pytest

from app.modules.criminal.record_profile import (
    ChargeCategory,
    RecordProfile,
    RecordType,
)


def _profile(**kwargs) -> RecordProfile:
    """Shorthand profile builder."""
    defaults = {
        "record_types": [RecordType.MISDEMEANOR],
        "charge_categories": [ChargeCategory.PROPERTY],
        "years_since_conviction": 5,
        "completed_sentence": True,
    }
    defaults.update(kwargs)
    return RecordProfile(**defaults)


class TestExpunctionEligibility:
    """Texas expunction (Art. 55) — complete record removal."""

    def test_arrest_only_eligible_now(self):
        from app.modules.criminal.texas_expunction import check_texas_record_clearing

        profile = _profile(record_types=[RecordType.ARREST_ONLY])
        result = check_texas_record_clearing(profile)
        assert result.expunction_eligible
        assert result.expunction_result.eligibility.value == "eligible_now"

    def test_acquittal_eligible_immediately(self):
        from app.modules.criminal.texas_expunction import check_texas_record_clearing

        profile = _profile(
            record_types=[RecordType.MISDEMEANOR],
            was_acquitted=True,
        )
        result = check_texas_record_clearing(profile)
        assert result.expunction_eligible

    def test_sex_offense_never_expungeable(self):
        from app.modules.criminal.texas_expunction import check_texas_record_clearing

        profile = _profile(charge_categories=[ChargeCategory.SEX_OFFENSE])
        result = check_texas_record_clearing(profile)
        assert not result.expunction_eligible


class TestNondisclosureEligibility:
    """Texas nondisclosure (Gov Code Ch. 411 E-1) — record sealing."""

    def test_misdemeanor_eligible_after_2_years(self):
        from app.modules.criminal.texas_expunction import check_texas_record_clearing

        profile = _profile(
            record_types=[RecordType.MISDEMEANOR],
            years_since_conviction=3,
            completed_deferred_adjudication=True,
        )
        result = check_texas_record_clearing(profile)
        assert result.nondisclosure_eligible

    def test_felony_eligible_after_5_years(self):
        from app.modules.criminal.texas_expunction import check_texas_record_clearing

        profile = _profile(
            record_types=[RecordType.FELONY],
            years_since_conviction=6,
            completed_deferred_adjudication=True,
        )
        result = check_texas_record_clearing(profile)
        assert result.nondisclosure_eligible

    def test_felony_not_eligible_before_wait(self):
        from app.modules.criminal.texas_expunction import check_texas_record_clearing

        profile = _profile(
            record_types=[RecordType.FELONY],
            years_since_conviction=3,
            completed_deferred_adjudication=True,
        )
        result = check_texas_record_clearing(profile)
        assert not result.nondisclosure_eligible
        assert result.nondisclosure_result.years_remaining > 0

    def test_family_violence_not_eligible_nondisclosure(self):
        from app.modules.criminal.texas_expunction import check_texas_record_clearing

        profile = _profile(
            charge_categories=[ChargeCategory.VIOLENCE],
            is_family_violence=True,
            completed_deferred_adjudication=True,
        )
        result = check_texas_record_clearing(profile)
        assert not result.nondisclosure_eligible

    def test_sex_offense_not_eligible_nondisclosure(self):
        from app.modules.criminal.texas_expunction import check_texas_record_clearing

        profile = _profile(
            charge_categories=[ChargeCategory.SEX_OFFENSE],
            completed_deferred_adjudication=True,
        )
        result = check_texas_record_clearing(profile)
        assert not result.nondisclosure_eligible


class TestFilingInfo:
    """Filing fee and legal aid contact info."""

    def test_filing_fee_is_280(self):
        from app.modules.criminal.texas_expunction import check_texas_record_clearing

        profile = _profile(record_types=[RecordType.ARREST_ONLY])
        result = check_texas_record_clearing(profile)
        assert "$280" in (result.expunction_result.filing_fee or "")

    def test_legal_aid_contact_in_steps(self):
        from app.modules.criminal.texas_expunction import check_texas_record_clearing

        profile = _profile(record_types=[RecordType.ARREST_ONLY])
        result = check_texas_record_clearing(profile)
        all_steps = " ".join(result.expunction_result.steps)
        assert "Legal Aid of NorthWest Texas" in all_steps or "817-336-3943" in all_steps


class TestNullProfile:
    """Edge cases."""

    def test_none_profile_returns_unknown(self):
        from app.modules.criminal.texas_expunction import check_texas_record_clearing

        result = check_texas_record_clearing(None)
        assert not result.expunction_eligible
        assert not result.nondisclosure_eligible
