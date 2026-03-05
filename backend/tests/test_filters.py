"""Tests for matching engine filters."""

import pytest

from app.modules.matching.filters import (
    apply_credit_filter,
    apply_transit_filter,
    apply_childcare_filter,
    get_certification_renewal,
)
from app.modules.matching.types import JobMatch, Resource


def _make_job(**overrides) -> JobMatch:
    defaults = {"title": "Clerk", "company": "ACME"}
    defaults.update(overrides)
    return JobMatch(**defaults)


def _make_resource(**overrides) -> Resource:
    defaults = {"id": 1, "name": "Provider A", "category": "childcare"}
    defaults.update(overrides)
    return Resource(**defaults)


class TestCreditFilter:
    def test_high_severity_flags_background_check_jobs(self):
        """HIGH severity: all jobs with credit_check_required != 'no' go to after_repair."""
        jobs = [
            _make_job(title="Bank Teller", credit_check_required="yes"),
            _make_job(title="Warehouse", credit_check_required="no"),
            _make_job(title="IT Admin", credit_check_required="unknown"),
        ]
        eligible_now, after_repair = apply_credit_filter(jobs, "high")
        assert len(eligible_now) == 1
        assert eligible_now[0].title == "Warehouse"
        assert len(after_repair) == 2

    def test_medium_severity_flags_finance_government(self):
        """MEDIUM: only finance/government jobs flagged."""
        jobs = [
            _make_job(title="Bank Teller", credit_check_required="yes"),
            _make_job(title="Warehouse", credit_check_required="no"),
            _make_job(title="Cook", credit_check_required="unknown"),
        ]
        eligible_now, after_repair = apply_credit_filter(jobs, "medium")
        assert len(after_repair) == 1
        assert after_repair[0].title == "Bank Teller"
        assert len(eligible_now) == 2

    def test_low_severity_all_eligible(self):
        """LOW: all jobs eligible now."""
        jobs = [
            _make_job(title="Bank Teller", credit_check_required="yes"),
            _make_job(title="Warehouse", credit_check_required="no"),
        ]
        eligible_now, after_repair = apply_credit_filter(jobs, "low")
        assert len(eligible_now) == 2
        assert len(after_repair) == 0


class TestTransitFilter:
    def test_filters_by_route_accessibility(self):
        """Jobs should get transit_accessible and route populated."""
        jobs = [_make_job(title="Clerk", location="Downtown Montgomery")]
        routes = [{"route_number": 3, "route_name": "East Side", "sunday": 0}]
        result = apply_transit_filter(jobs, routes, "36101")
        assert len(result) == 1
        assert result[0].transit_accessible is True

    def test_flags_sunday_jobs_no_transit(self):
        """Jobs flagged as Sunday should note no transit."""
        jobs = [_make_job(title="Sunday Shift", location="Sunday required")]
        routes = [{"route_number": 3, "route_name": "East Side", "sunday": 0}]
        result = apply_transit_filter(jobs, routes, "36101")
        assert result[0].eligible_after == "requires personal transportation"

    def test_flags_night_shift_no_transit(self):
        """Night shift jobs should note transit unavailable."""
        jobs = [_make_job(title="Night Guard", location="Night shift 10pm-6am")]
        routes = [{"route_number": 3, "route_name": "East Side", "sunday": 0}]
        result = apply_transit_filter(jobs, routes, "36101")
        assert result[0].eligible_after == "requires personal transportation"


class TestChildcareFilter:
    def test_filters_by_proximity_to_home_and_work(self):
        """Should return childcare resources matching user/employer zip area."""
        resources = [
            _make_resource(id=1, name="Near Home", address="123 Main St, Montgomery, AL 36104"),
            _make_resource(id=2, name="Far Away", address="456 Rural Rd, Dothan, AL 36301"),
            _make_resource(id=3, name="Near Work", address="789 Commerce Dr, Montgomery, AL 36106"),
        ]
        result = apply_childcare_filter(resources, "36104", ["36106"])
        # Should include resources with Montgomery zips
        names = [r.name for r in result]
        assert "Near Home" in names
        assert "Near Work" in names


class TestCertificationRenewal:
    def test_parses_cna_from_work_history(self):
        """Should detect CNA in work history."""
        results = get_certification_renewal("Former CNA at Baptist Hospital")
        assert len(results) >= 1
        assert results[0]["certification_type"] == "CNA"

    def test_parses_cdl_from_work_history(self):
        """Should detect CDL in work history."""
        results = get_certification_renewal("CDL truck driver for 5 years")
        assert len(results) >= 1
        assert results[0]["certification_type"] == "CDL"

    def test_returns_renewal_body_info(self):
        """Should include renewal body with name."""
        results = get_certification_renewal("Expired CNA certification")
        assert "renewal_body" in results[0]
        assert "name" in results[0]["renewal_body"]

    def test_matches_local_training_program(self):
        """Should include training program info."""
        results = get_certification_renewal("CNA work history")
        assert "training_program" in results[0]
        assert "name" in results[0]["training_program"]

    def test_generates_ordered_action_steps(self):
        """Should return list of action steps."""
        results = get_certification_renewal("CNA expired")
        assert "steps" in results[0]
        assert len(results[0]["steps"]) > 0
        assert "estimated_days" in results[0]
