"""Tests verifying eligibility rules include Fort Worth resources."""

from app.modules.resources.eligibility import ELIGIBILITY_RULES


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
