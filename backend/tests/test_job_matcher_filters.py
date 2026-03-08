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


class TestTransitFilter:
    def test_job_near_stop_is_accessible(self):
        """Jobs near a transit stop should be marked transit_accessible=True."""
        from app.modules.matching.job_matcher import _filter_by_transit

        jobs = [_make_job("Cashier", location="3801 Eastern Blvd, Montgomery, AL 36116")]
        stops = [{"lat": 32.35, "lng": -86.27, "stop_name": "Eastern Blvd"}]
        result = _filter_by_transit(jobs, transit_dependent=True, transit_stops=stops)
        assert result[0]["transit_accessible"] is True

    def test_job_far_from_stops_not_accessible(self):
        """Jobs far from all transit stops should be marked transit_accessible=False."""
        from app.modules.matching.job_matcher import _filter_by_transit

        jobs = [_make_job("Rural Worker", location="999 Remote Rd, Prattville, AL 36067")]
        stops = [{"lat": 32.35, "lng": -86.27, "stop_name": "Downtown"}]
        result = _filter_by_transit(jobs, transit_dependent=True, transit_stops=stops)
        assert result[0]["transit_accessible"] is False

    def test_sunday_job_flagged_for_transit_users(self):
        """Jobs requiring Sunday work should flag transit users (no Sunday service)."""
        from app.modules.matching.job_matcher import _filter_by_transit

        jobs = [_make_job("Driver", description="Tuesday-Saturday including some Sundays")]
        stops = [{"lat": 32.37, "lng": -86.30, "stop_name": "Main"}]
        result = _filter_by_transit(jobs, transit_dependent=True, transit_stops=stops)
        assert result[0]["sunday_flag"] is True

    def test_non_transit_dependent_skips_filter(self):
        """Non-transit-dependent users get all jobs marked accessible."""
        from app.modules.matching.job_matcher import _filter_by_transit

        jobs = [_make_job("Remote", location="Far away")]
        result = _filter_by_transit(jobs, transit_dependent=False, transit_stops=[])
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
            with patch("app.modules.matching.job_matcher._get_transit_stops", return_value=[]):
                result = await match_jobs(profile, mock_session)

        assert result == []
