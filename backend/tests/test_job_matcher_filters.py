"""Tests for job matcher filter pipeline."""

import pytest

from app.modules.matching.types import AvailableHours


def _make_job(title="Test Job", company=None, description="", credit_check="not_required", location=None):
    """Helper to create a job dict matching DB row shape."""
    return {
        "id": 1,
        "title": title,
        "company": company,
        "location": location,
        "description": description,
        "url": None,
        "source": "seed",
        "scraped_at": "2026-03-01T00:00:00Z",
        "expires_at": None,
        "credit_check": credit_check,
    }


class TestIndustryFilter:
    def test_matching_industry_flagged(self):
        """Jobs matching target industry should get industry_match=True."""
        from app.modules.matching.job_matcher import _filter_by_industry

        jobs = [_make_job("Certified Nursing Assistant", "Baptist Health", "CNA position")]
        result = _filter_by_industry(jobs, ["healthcare"])
        assert result[0]["industry_match"] is True

    def test_non_matching_industry_not_flagged(self):
        """Jobs not matching target industry should get industry_match=False."""
        from app.modules.matching.job_matcher import _filter_by_industry

        jobs = [_make_job("Warehouse Associate", "Amazon", "Pick and pack")]
        result = _filter_by_industry(jobs, ["healthcare"])
        assert result[0]["industry_match"] is False

    def test_no_target_industries_all_unflagged(self):
        """With no target industries, all jobs get industry_match=False."""
        from app.modules.matching.job_matcher import _filter_by_industry

        jobs = [_make_job("CNA", "Hospital")]
        result = _filter_by_industry(jobs, [])
        assert result[0]["industry_match"] is False


class TestScheduleFilter:
    def test_night_shift_deprioritized_for_daytime(self):
        """Night shift jobs should get schedule_conflict=True for daytime users."""
        from app.modules.matching.job_matcher import _filter_by_schedule

        jobs = [_make_job("Stocker", description="Overnight stocking 10pm-7am")]
        result = _filter_by_schedule(jobs, AvailableHours.DAYTIME)
        assert result[0]["schedule_conflict"] is True

    def test_day_shift_ok_for_daytime(self):
        """Day shift jobs should not conflict for daytime users."""
        from app.modules.matching.job_matcher import _filter_by_schedule

        jobs = [_make_job("Cashier", description="Day shift 8am-4pm")]
        result = _filter_by_schedule(jobs, AvailableHours.DAYTIME)
        assert result[0]["schedule_conflict"] is False

    def test_flexible_never_conflicts(self):
        """Flexible schedule users should never have schedule conflicts."""
        from app.modules.matching.job_matcher import _filter_by_schedule

        jobs = [_make_job("Stocker", description="Night shift 11pm-7am")]
        result = _filter_by_schedule(jobs, AvailableHours.FLEXIBLE)
        assert result[0]["schedule_conflict"] is False


def _make_stop(name, lat, lng, route_id=1, route_name="Route 1"):
    """Build a stop-with-route dict for transit filter tests."""
    return {
        "stop_name": name, "lat": lat, "lng": lng,
        "route_id": route_id, "route_number": route_id, "route_name": route_name,
        "weekday_start": "05:00", "weekday_end": "21:00", "saturday": 1, "sunday": 0,
    }


class TestTransitFilter:
    def test_job_near_stop_is_accessible(self):
        """Jobs with coordinates near a transit stop should be accessible."""
        from app.modules.matching.job_matcher import _filter_by_transit

        jobs = [{**_make_job("Cashier", location="Montgomery, AL"), "lat": 32.35, "lng": -86.27}]
        stops = [_make_stop("Eastern Blvd", 32.35, -86.27)]
        result = _filter_by_transit(jobs, transit_dependent=True, stops_with_routes=stops)
        assert result[0]["transit_accessible"] is True

    def test_job_far_from_stops_not_accessible(self):
        """Jobs far from all transit stops should not be accessible."""
        from app.modules.matching.job_matcher import _filter_by_transit

        jobs = [{**_make_job("Rural Worker"), "lat": 33.0, "lng": -85.0}]
        stops = [_make_stop("Downtown", 32.35, -86.27)]
        result = _filter_by_transit(jobs, transit_dependent=True, stops_with_routes=stops)
        assert result[0]["transit_accessible"] is False

    def test_sunday_gap_flagged_for_daytime_shift(self):
        """MATS has no Sunday service — all transit-dependent jobs get sunday_flag."""
        from app.modules.matching.job_matcher import _filter_by_transit

        jobs = [{**_make_job("Cashier"), "lat": 32.35, "lng": -86.27}]
        stops = [_make_stop("Downtown", 32.35, -86.27)]
        result = _filter_by_transit(jobs, transit_dependent=True, stops_with_routes=stops)
        assert result[0]["sunday_flag"] is True  # all MATS routes have sunday=0

    def test_keyword_fallback_for_jobs_without_coords(self):
        """Jobs without lat/lng fall back to keyword-based transit check."""
        from app.modules.matching.job_matcher import _filter_by_transit

        jobs = [_make_job("Driver", description="Work includes Sundays in Montgomery")]
        stops = [_make_stop("Main", 32.37, -86.30)]
        result = _filter_by_transit(jobs, transit_dependent=True, stops_with_routes=stops)
        assert result[0]["sunday_flag"] is True
        assert result[0]["transit_accessible"] is True  # "montgomery" in text

    def test_non_transit_dependent_skips_filter(self):
        """Non-transit-dependent users get all jobs marked accessible."""
        from app.modules.matching.job_matcher import _filter_by_transit

        jobs = [_make_job("Remote", location="Far away")]
        result = _filter_by_transit(jobs, transit_dependent=False, stops_with_routes=[])
        assert result[0]["transit_accessible"] is True
        assert result[0]["sunday_flag"] is False


class TestCreditAnnotation:
    def test_credit_required_annotated(self):
        """Jobs with credit_check=required should be annotated."""
        from app.modules.matching.job_matcher import _annotate_credit

        jobs = [_make_job("Clerk", credit_check="required")]
        result = _annotate_credit(jobs)
        assert result[0]["credit_blocked"] is True

    def test_credit_not_required_not_blocked(self):
        """Jobs with credit_check=not_required should not be blocked."""
        from app.modules.matching.job_matcher import _annotate_credit

        jobs = [_make_job("Cashier", credit_check="not_required")]
        result = _annotate_credit(jobs)
        assert result[0]["credit_blocked"] is False


class TestRecordEnrichment:
    def test_record_enrichment_adds_fields(self):
        """Jobs should get record fields when annotated with record data."""
        from app.modules.criminal.employer_policy import EmployerPolicy
        from app.modules.criminal.job_filter import filter_jobs_by_record
        from app.modules.criminal.record_profile import (
            ChargeCategory,
            RecordProfile,
            RecordType,
        )

        policies = [
            EmployerPolicy(
                employer_name="Walmart",
                fair_chance=True,
                excluded_charges=[],
                lookback_years=7,
                background_check_timing="post_offer",
            ),
        ]
        profile = RecordProfile(
            record_types=[RecordType.MISDEMEANOR],
            charge_categories=[ChargeCategory.THEFT],
            years_since_conviction=10,
        )
        jobs = [_make_job("Cashier", company="Walmart")]
        result = filter_jobs_by_record(jobs, profile, policies)
        assert result[0]["fair_chance"] is True
        assert result[0]["record_eligible"] is True
        assert result[0]["background_check_timing"] == "post_offer"

    def test_record_enrichment_no_profile_passthrough(self):
        """No record profile → defaults (eligible, not fair-chance)."""
        from app.modules.criminal.job_filter import filter_jobs_by_record

        jobs = [_make_job("Cashier", company="Walmart")]
        result = filter_jobs_by_record(jobs, None, [])
        assert result[0]["fair_chance"] is False
        assert result[0]["record_eligible"] is True


class TestMatchJobsEmpty:
    @pytest.mark.anyio
    async def test_empty_listings_returns_empty(self, test_engine):
        """match_jobs with no job listings in DB should return empty list."""
        from unittest.mock import AsyncMock

        from app.modules.matching.job_matcher import match_jobs
        from app.modules.matching.types import UserProfile, BarrierType, BarrierSeverity, EmploymentStatus

        profile = UserProfile(
            session_id="test",
            zip_code="36104",
            employment_status=EmploymentStatus.UNEMPLOYED,
            barrier_count=1,
            primary_barriers=[BarrierType.CREDIT],
            barrier_severity=BarrierSeverity.HIGH,
            needs_credit_assessment=True,
            transit_dependent=True,
            schedule_type="daytime",
            work_history="CNA for 3 years",
            target_industries=["healthcare"],
        )
        # Mock db_session to return empty job listings and empty transit stops
        mock_session = AsyncMock()
        mock_session.execute.return_value.fetchall.return_value = []
        mock_session.execute.return_value.all.return_value = []

        # Use a patched version to return empty data
        from unittest.mock import patch
        with patch("app.modules.matching.job_matcher.get_all_job_listings", return_value=[]):
            with patch("app.modules.matching.job_matcher._get_stops_with_routes", return_value=[]):
                result = await match_jobs(profile, mock_session)

        assert result == []
