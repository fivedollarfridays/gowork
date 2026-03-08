"""Contract tests: montgowork consumer ↔ credit-assessment provider.

Validates that the credit-assessment API's actual response schema matches
what MontGoWork's CreditAssessmentResult model expects. If credit-assessment
changes its response shape, these tests break BEFORE production does.

Run with: pytest backend/tests/test_contract_credit_api.py -v
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.modules.credit.types import CreditAssessmentResult, SimpleCreditRequest

# ---------------------------------------------------------------------------
# Locate sibling repo
# ---------------------------------------------------------------------------

_CREDIT_REPO = Path(__file__).resolve().parents[3] / "credit-assessment"
_PROVIDER_TYPES = _CREDIT_REPO / "src" / "modules" / "credit" / "types.py"

SIBLING_AVAILABLE = _CREDIT_REPO.is_dir() and _PROVIDER_TYPES.is_file()


def _skip_if_no_sibling():
    if not SIBLING_AVAILABLE:
        pytest.skip("credit-assessment sibling repo not found")


# ---------------------------------------------------------------------------
# Canonical provider response (matches montgowork-credit-integration.md §5)
# ---------------------------------------------------------------------------

MARIA_RESPONSE: dict = {
    "barrier_severity": "high",
    "barrier_details": [
        {
            "severity": "high",
            "description": "1 collection account(s) on file",
            "affected_accounts": [],
            "estimated_resolution_days": 90,
        },
    ],
    "readiness": {
        "score": 20,
        "fico_score": 520,
        "score_band": "very_poor",
        "factors": {
            "payment_history": 0.72,
            "utilization": 0.15,
            "credit_age": 0.429,
            "credit_mix": 0.8,
            "new_credit": 0.7,
        },
    },
    "thresholds": [
        {
            "threshold_name": "Poor Credit",
            "threshold_score": 600,
            "estimated_days": 400,
            "already_met": False,
            "confidence": "low",
        },
    ],
    "dispute_pathway": {
        "steps": [
            {
                "step_number": 1,
                "action": "Validate and dispute collection",
                "description": "File dispute for collection",
                "legal_basis": "FDCPA Section 809",
                "estimated_days": 30,
                "priority": "critical",
            },
        ],
        "total_estimated_days": 150,
        "statutes_cited": ["15 U.S.C. § 1681i"],
        "legal_theories": ["fcra_611_reinvestigation"],
    },
    "eligibility": [
        {
            "product_name": "Secured Credit Card",
            "category": "credit_card",
            "required_score": 300,
            "status": "eligible",
            "gap_points": 0,
            "estimated_days_to_eligible": None,
            "blocking_factors": [],
        },
    ],
    "disclaimer": "This credit assessment is provided for educational purposes only.",
}


# ---------------------------------------------------------------------------
# Contract: consumer model accepts provider response
# ---------------------------------------------------------------------------


class TestConsumerAcceptsProviderResponse:
    """MontGoWork's CreditAssessmentResult must parse the provider's output."""

    def test_parses_canonical_response(self):
        """Consumer model accepts the canonical Maria response from the integration guide."""
        result = CreditAssessmentResult(**MARIA_RESPONSE)
        assert result.barrier_severity == "high"
        assert result.readiness["score"] == 20
        assert len(result.dispute_pathway["steps"]) == 1
        assert result.disclaimer.startswith("This credit assessment")

    def test_parses_minimal_response(self):
        """Consumer model accepts a minimal valid response."""
        minimal = {
            "barrier_severity": "low",
            "barrier_details": [],
            "readiness": {"score": 80, "fico_score": 720, "score_band": "good"},
            "thresholds": [],
            "dispute_pathway": {"steps": [], "total_estimated_days": 0},
            "eligibility": [],
            "disclaimer": "Disclaimer text.",
        }
        result = CreditAssessmentResult(**minimal)
        assert result.barrier_severity == "low"

    def test_all_required_fields_present(self):
        """Consumer model requires all 7 top-level fields."""
        required = {
            "barrier_severity",
            "barrier_details",
            "readiness",
            "thresholds",
            "dispute_pathway",
            "eligibility",
            "disclaimer",
        }
        model_fields = set(CreditAssessmentResult.model_fields.keys())
        assert required == model_fields, (
            f"Field mismatch — provider contract changed. "
            f"Missing: {required - model_fields}, Extra: {model_fields - required}"
        )


# ---------------------------------------------------------------------------
# Contract: consumer request matches provider's SimpleCreditProfile
# ---------------------------------------------------------------------------


class TestConsumerRequestMatchesProvider:
    """MontGoWork's SimpleCreditRequest fields must match the provider's input."""

    def test_request_has_required_fields(self):
        """All fields the provider expects must exist in our request model."""
        provider_fields = {
            "credit_score",
            "utilization_percent",
            "total_accounts",
            "open_accounts",
            "negative_items",
            "payment_history_percent",
            "oldest_account_months",
            "total_balance",
            "total_credit_limit",
            "monthly_payments",
        }
        consumer_fields = set(SimpleCreditRequest.model_fields.keys())
        missing = provider_fields - consumer_fields
        assert not missing, f"Consumer missing provider fields: {missing}"

    def test_no_extra_fields_sent(self):
        """Consumer should not send fields the provider doesn't expect."""
        provider_fields = {
            "credit_score",
            "utilization_percent",
            "total_accounts",
            "open_accounts",
            "negative_items",
            "payment_history_percent",
            "oldest_account_months",
            "total_balance",
            "total_credit_limit",
            "monthly_payments",
        }
        consumer_fields = set(SimpleCreditRequest.model_fields.keys())
        extra = consumer_fields - provider_fields
        assert not extra, f"Consumer sends unknown fields: {extra}"

    def test_score_bounds_match(self):
        """Credit score bounds should match provider's validation."""
        field = SimpleCreditRequest.model_fields["credit_score"]
        metadata = field.metadata
        ge_vals = [getattr(m, "ge", None) for m in metadata if hasattr(m, "ge")]
        le_vals = [getattr(m, "le", None) for m in metadata if hasattr(m, "le")]
        assert 300 in ge_vals, "credit_score ge should be 300"
        assert 850 in le_vals, "credit_score le should be 850"


# ---------------------------------------------------------------------------
# Contract: provider schema hasn't drifted (reads sibling repo source)
# ---------------------------------------------------------------------------


class TestProviderSchemaStability:
    """Verify the provider's CreditAssessmentResult fields haven't changed."""

    def test_provider_response_fields_unchanged(self):
        """Provider's CreditAssessmentResult must still have the 7 expected fields."""
        _skip_if_no_sibling()

        # Import provider's types via subprocess to avoid sys.path pollution
        script = (
            "import json, sys; sys.path.insert(0, 'src'); "
            "from modules.credit.types import CreditAssessmentResult; "
            "print(json.dumps(list(CreditAssessmentResult.model_fields.keys())))"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=str(_CREDIT_REPO),
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Provider import failed: {result.stderr}"
        provider_fields = set(json.loads(result.stdout))

        expected = {
            "barrier_severity",
            "barrier_details",
            "readiness",
            "thresholds",
            "dispute_pathway",
            "eligibility",
            "disclaimer",
        }
        assert provider_fields == expected, (
            f"Provider schema changed! "
            f"Added: {provider_fields - expected}, Removed: {expected - provider_fields}"
        )

    def test_provider_simple_input_fields_unchanged(self):
        """Provider's SimpleCreditProfile must still accept our fields."""
        _skip_if_no_sibling()

        script = (
            "import json, sys; sys.path.insert(0, 'src'); "
            "from modules.credit.assess_routes import SimpleCreditProfile; "
            "print(json.dumps(list(SimpleCreditProfile.model_fields.keys())))"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=str(_CREDIT_REPO),
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Provider import failed: {result.stderr}"
        provider_fields = set(json.loads(result.stdout))

        our_fields = set(SimpleCreditRequest.model_fields.keys())
        missing = our_fields - provider_fields
        assert not missing, (
            f"Provider no longer accepts fields we send: {missing}"
        )
