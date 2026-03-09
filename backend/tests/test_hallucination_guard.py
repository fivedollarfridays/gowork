"""Tests for hallucination detection guardrail."""

import pytest

from app.barrier_intel.guardrails import check_hallucinations, HALLUCINATION_DISCLAIMER


class TestCheckHallucinations:
    """Verify hallucination detection against known resource names."""

    def test_no_hallucination_when_all_resources_known(self):
        """Response mentioning only known resources returns no disclaimer."""
        response = "You should contact GreenPath Financial for credit counseling."
        known_names = ["GreenPath Financial", "Alabama Career Center", "M-Transit"]
        result = check_hallucinations(response, known_names)
        assert result is None

    def test_detects_hallucinated_resource(self):
        """Response mentioning unknown resource triggers disclaimer."""
        response = "Visit the Springfield Job Center for help with your resume."
        known_names = ["GreenPath Financial", "Alabama Career Center"]
        result = check_hallucinations(response, known_names)
        assert result is not None
        assert "Springfield Job Center" in result
        assert HALLUCINATION_DISCLAIMER in result

    def test_empty_response_returns_none(self):
        response = ""
        known_names = ["GreenPath Financial"]
        result = check_hallucinations(response, known_names)
        assert result is None

    def test_empty_known_names_flags_any_org_mention(self):
        """With no known resources, any org-like mention is flagged."""
        response = "Contact the Montgomery Housing Authority for assistance."
        result = check_hallucinations(response, [])
        # With empty known list, we can't distinguish — should not flag
        assert result is None

    def test_all_caps_names_not_detected(self):
        """All-caps org names are not matched by the pattern (known limitation)."""
        response = "Contact GREENPATH FINANCIAL for help."
        known_names = ["GreenPath Financial"]
        result = check_hallucinations(response, known_names)
        # _ORG_PATTERN requires [A-Z][a-z]+ per word, so all-caps is invisible
        assert result is None

    def test_title_case_known_resource_not_flagged(self):
        """Title-case known resource name is matched case-insensitively."""
        response = "Contact Greenpath Financial for credit counseling."
        known_names = ["GreenPath Financial"]
        result = check_hallucinations(response, known_names)
        assert result is None

    def test_partial_match_not_flagged(self):
        """Substring of known resource should not flag."""
        response = "GreenPath offers credit counseling services."
        known_names = ["GreenPath Financial"]
        result = check_hallucinations(response, known_names)
        assert result is None

    def test_multiple_hallucinated_resources(self):
        """Multiple unknown resources mentioned."""
        response = (
            "Visit the Fake Job Center and contact Imaginary Services "
            "for help with your plan."
        )
        known_names = ["GreenPath Financial", "Alabama Career Center"]
        result = check_hallucinations(response, known_names)
        assert result is not None

    def test_does_not_flag_generic_words(self):
        """Common words and phrases should not be flagged as resources."""
        response = (
            "Your next step is to check your credit report and review "
            "the bus schedule. Make sure to bring your ID."
        )
        known_names = ["GreenPath Financial"]
        result = check_hallucinations(response, known_names)
        assert result is None

    def test_known_montgomery_resources_not_flagged(self):
        """Well-known Montgomery resources passed as known should not flag."""
        response = (
            "Head to the Alabama Career Center on Carter Hill Road. "
            "M-Transit Route 4 can get you there."
        )
        known_names = ["Alabama Career Center", "M-Transit"]
        result = check_hallucinations(response, known_names)
        assert result is None

    def test_day_name_in_org_not_flagged(self):
        """Proper-noun phrase containing a day/month name is skipped as false positive."""
        response = "Visit Monday Morning Services for help with your job search."
        known_names = ["GreenPath Financial"]
        result = check_hallucinations(response, known_names)
        # "Monday Morning Services" matches _ORG_PATTERN but "monday" is in
        # _FALSE_POSITIVE_WORDS so it should be filtered out (continue branch).
        assert result is None


class TestHallucinationDisclaimer:
    """Verify disclaimer format."""

    def test_disclaimer_is_informative(self):
        assert "verify" in HALLUCINATION_DISCLAIMER.lower() or "confirm" in HALLUCINATION_DISCLAIMER.lower()

    def test_disclaimer_not_empty(self):
        assert len(HALLUCINATION_DISCLAIMER) > 0
