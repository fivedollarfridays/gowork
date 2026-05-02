"""Tests verifying eligibility rules include Fort Worth resources +
that the runtime active rule set is city-scoped (defense-in-depth so
Montgomery rules can never match in a Fort Worth request, and vice
versa, even if a stale resource sneaks through a future regression)."""

import pytest

from app.cities.config import (
    clear_city_context,
    get_city_config,
    set_city_context,
)
from app.modules.matching.types import Resource
from app.modules.resources.eligibility import (
    ELIGIBILITY_RULES,
    _active_rules_lower,
    _match_rule,
)


class TestEligibilityRulesIncludeFortWorth:
    """Verify Fort Worth resources are in eligibility rules."""

    def test_workforce_solutions_in_rules(self):
        """Workforce Solutions for Tarrant County should be recognized."""
        assert any(
            "workforce solutions" in key.lower()
            for key in ELIGIBILITY_RULES
        ), "Workforce Solutions should be in ELIGIBILITY_RULES"

    def test_tarrant_county_college_in_rules(self):
        """Tarrant County College should be recognized."""
        assert any(
            "tarrant county college" in key.lower()
            for key in ELIGIBILITY_RULES
        ), "Tarrant County College should be in ELIGIBILITY_RULES"

    def test_trinity_metro_in_rules(self):
        """Trinity Metro should be recognized."""
        assert any(
            "trinity metro" in key.lower()
            for key in ELIGIBILITY_RULES
        ), "Trinity Metro should be in ELIGIBILITY_RULES"

    def test_jps_health_in_rules(self):
        """JPS Health Network should be recognized."""
        assert any(
            "jps" in key.lower()
            for key in ELIGIBILITY_RULES
        ), "JPS Health Network should be in ELIGIBILITY_RULES"


class TestEligibilityCityIsolation:
    """Runtime active-rule set MUST scope to the active city's state.

    Locks in the defense-in-depth fix: even if a stale Montgomery
    resource sneaks into a Fort Worth response (city-tagging
    regression), its eligibility rule should NOT match because the
    AL rules are not loaded into the active set when state == "TX".
    Same in reverse.
    """

    def teardown_method(self):
        """Always clear the per-request city context after each test."""
        clear_city_context()

    def test_active_rules_in_tx_exclude_alabama_rules(self):
        set_city_context("fort-worth")
        assert get_city_config().state == "TX"
        active = _active_rules_lower()
        # Universal rules present
        assert "211 helpline" in active
        # FW rules present
        assert "workforce solutions for tarrant county" in active
        # AL rules MUST be absent
        assert "onealabama" not in active
        assert "montgomery career center" not in active
        assert "trenholm state" not in active
        assert "mats" not in active

    def test_active_rules_in_al_exclude_fortworth_rules(self):
        set_city_context("montgomery")
        assert get_city_config().state == "AL"
        active = _active_rules_lower()
        # Universal rules present
        assert "211 helpline" in active
        # AL rules present
        assert "onealabama" in active
        assert "montgomery career center" in active
        # FW rules MUST be absent
        assert "workforce solutions for tarrant county" not in active
        assert "trinity metro" not in active
        assert "jps" not in active

    def test_alabama_resource_unmatchable_in_fortworth_context(self):
        """A stale AL-tagged Resource sneaking into a FW response gets
        UNKNOWN status, never falsely LIKELY."""
        set_city_context("fort-worth")
        leak = Resource(
            id=999,
            name="OneAlabama Community Resource Network",
            category="social_service",
            address="dummy",
            phone="dummy",
            services=[],
            health_status="healthy",
        )
        # _match_rule returns None when no AL rule is active
        assert _match_rule(leak.name) is None

    def test_fortworth_resource_unmatchable_in_montgomery_context(self):
        set_city_context("montgomery")
        leak = Resource(
            id=999,
            name="Workforce Solutions for Tarrant County",
            category="social_service",
            address="dummy",
            phone="dummy",
            services=[],
            health_status="healthy",
        )
        assert _match_rule(leak.name) is None
