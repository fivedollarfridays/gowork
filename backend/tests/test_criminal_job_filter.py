"""Tests for criminal record job filter — T26.3."""

from app.modules.criminal.employer_policy import EmployerPolicy
from app.modules.criminal.job_filter import (
    enrich_job_with_record_status,
    filter_jobs_by_record,
)
from app.modules.criminal.record_profile import (
    ChargeCategory,
    RecordProfile,
    RecordType,
)


_POLICIES = [
    EmployerPolicy(
        employer_name="Walmart",
        fair_chance=True,
        excluded_charges=["sex_offense"],
        lookback_years=7,
        background_check_timing="post_offer",
    ),
    EmployerPolicy(
        employer_name="Baptist Health",
        fair_chance=False,
        excluded_charges=["violence", "sex_offense", "drug"],
        lookback_years=10,
        background_check_timing="pre_offer",
    ),
    EmployerPolicy(
        employer_name="Goodwill",
        fair_chance=True,
        excluded_charges=[],
        background_check_timing="post_offer",
    ),
]


class TestEnrichJobWithRecordStatus:
    def test_fair_chance_employer_match(self):
        """Job from fair-chance employer should get fair_chance=True."""
        job = {"title": "Cashier", "company": "Walmart"}
        profile = RecordProfile(
            record_types=[RecordType.MISDEMEANOR],
            charge_categories=[ChargeCategory.THEFT],
            years_since_conviction=10,
        )
        result = enrich_job_with_record_status(job, profile, _POLICIES)
        assert result["fair_chance"] is True
        assert result["record_eligible"] is True
        assert result["background_check_timing"] == "post_offer"

    def test_excluded_charge_blocks(self):
        """Job from employer excluding user's charges → not eligible."""
        job = {"title": "Nurse Aid", "company": "Baptist Health"}
        profile = RecordProfile(
            record_types=[RecordType.FELONY],
            charge_categories=[ChargeCategory.VIOLENCE],
            years_since_conviction=3,
        )
        result = enrich_job_with_record_status(job, profile, _POLICIES)
        assert result["record_eligible"] is False
        assert result["fair_chance"] is False

    def test_no_matching_policy_defaults(self):
        """Job from unknown employer → unknown status."""
        job = {"title": "Clerk", "company": "Unknown Corp"}
        profile = RecordProfile(
            record_types=[RecordType.FELONY],
            charge_categories=[ChargeCategory.THEFT],
        )
        result = enrich_job_with_record_status(job, profile, _POLICIES)
        assert result["fair_chance"] is False
        assert result["record_eligible"] is True  # default: give benefit of doubt
        assert result["background_check_timing"] is None

    def test_expunged_always_eligible(self):
        """Expunged records → always eligible, no note."""
        job = {"title": "Nurse Aid", "company": "Baptist Health"}
        profile = RecordProfile(record_types=[RecordType.EXPUNGED])
        result = enrich_job_with_record_status(job, profile, _POLICIES)
        assert result["record_eligible"] is True
        assert result["fair_chance"] is False  # employer isn't fair-chance

    def test_no_record_passthrough(self):
        """No record profile → pass-through with defaults."""
        job = {"title": "Cashier", "company": "Walmart"}
        result = enrich_job_with_record_status(job, None, _POLICIES)
        assert result["fair_chance"] is False
        assert result["record_eligible"] is True
        assert result["record_note"] is None


class TestFilterJobsByRecord:
    def test_no_record_returns_all_jobs(self):
        """No record profile → all jobs returned unchanged."""
        jobs = [
            {"title": "Job A", "company": "Walmart"},
            {"title": "Job B", "company": "Baptist Health"},
        ]
        result = filter_jobs_by_record(jobs, None, _POLICIES)
        assert len(result) == 2

    def test_enriches_all_jobs(self):
        """All jobs should have fair_chance and record_eligible fields."""
        jobs = [
            {"title": "Job A", "company": "Walmart"},
            {"title": "Job B", "company": "Goodwill"},
        ]
        profile = RecordProfile(
            record_types=[RecordType.MISDEMEANOR],
            charge_categories=[ChargeCategory.THEFT],
            years_since_conviction=10,
        )
        result = filter_jobs_by_record(jobs, profile, _POLICIES)
        for job in result:
            assert "fair_chance" in job
            assert "record_eligible" in job

    def test_fair_chance_jobs_sorted_first(self):
        """Fair-chance eligible jobs should appear before non-fair-chance."""
        jobs = [
            {"title": "Job A", "company": "Baptist Health"},
            {"title": "Job B", "company": "Walmart"},
            {"title": "Job C", "company": "Goodwill"},
        ]
        profile = RecordProfile(
            record_types=[RecordType.MISDEMEANOR],
            charge_categories=[ChargeCategory.THEFT],
            years_since_conviction=10,
        )
        result = filter_jobs_by_record(jobs, profile, _POLICIES)
        # Fair-chance jobs first, then others
        fair_chance_indices = [i for i, j in enumerate(result) if j["fair_chance"]]
        non_fair_indices = [i for i, j in enumerate(result) if not j["fair_chance"]]
        if fair_chance_indices and non_fair_indices:
            assert max(fair_chance_indices) < min(non_fair_indices)

    def test_empty_jobs_list(self):
        """Empty jobs list → empty result."""
        profile = RecordProfile(record_types=[RecordType.FELONY])
        result = filter_jobs_by_record([], profile, _POLICIES)
        assert result == []


class TestEnrichJobEdgeCases:
    """Cover remaining branches in job_filter.py."""

    def test_enrich_job_no_company_gets_defaults(self):
        """Job with company=None -> _find_policy returns None -> defaults."""
        job = {"title": "Clerk", "company": None}
        profile = RecordProfile(
            record_types=[RecordType.FELONY],
            charge_categories=[ChargeCategory.THEFT],
            years_since_conviction=5,
        )
        result = enrich_job_with_record_status(job, profile, _POLICIES)
        assert result["fair_chance"] is False
        assert result["record_eligible"] is True
        assert result["background_check_timing"] is None
        assert result["record_note"] is None

    def test_record_note_charge_type_exclusion(self):
        """Excluded charge with no lookback -> 'Not eligible based on charge type'."""
        # Policy with excluded charges but NO lookback_years
        policies = [
            EmployerPolicy(
                employer_name="SecureCo",
                fair_chance=False,
                excluded_charges=["violence"],
                lookback_years=None,
                background_check_timing="pre_offer",
            ),
        ]
        profile = RecordProfile(
            record_types=[RecordType.FELONY],
            charge_categories=[ChargeCategory.VIOLENCE],
            years_since_conviction=2,
        )
        job = {"title": "Guard", "company": "SecureCo"}
        result = enrich_job_with_record_status(job, profile, policies)
        assert result["record_eligible"] is False
        assert result["record_note"] == "Not eligible based on charge type"
