"""Tests for ZIP-agnostic assessment pipeline.

The system must be agnostic: a user entering an Alabama ZIP (36104) or
a Texas/Fort Worth ZIP (76102) should both flow through the full
assessment → matching → plan pipeline without crashing.

Four concerns tested:
1. normalize_expungement() flattens TexasRecordClearingResult into a
   single ExpungementResult before it enters BarrierCard (no Union).
2. ZIP validation accepts ZIPs from ANY configured city, not just the
   server's default city.
3. The per-request city context resolves the correct city from the ZIP
   so downstream routers (criminal, benefits, jobs) use the right state.
4. BarrierCard.expungement remains Optional[ExpungementResult] — the
   normalizer runs before construction, not after.
"""

import pytest

from app.modules.criminal.expungement import (
    ExpungementEligibility,
    ExpungementResult,
)
from app.modules.criminal.texas_expunction import TexasRecordClearingResult
from app.modules.matching.barrier_cards import normalize_expungement
from app.modules.matching.types import BarrierCard, BarrierSeverity, BarrierType


# ── Part 1: normalize_expungement ──────────────────────────────────


class TestNormalizeExpungement:
    """normalize_expungement() flattens TX results to ExpungementResult."""

    def test_passthrough_alabama_result(self):
        """Alabama ExpungementResult passes through unchanged."""
        result = ExpungementResult(
            eligibility=ExpungementEligibility.ELIGIBLE_NOW,
            years_remaining=0,
            steps=["Contact Legal Services Alabama"],
            filing_fee="$300",
        )
        assert normalize_expungement(result) is result

    def test_none_returns_none(self):
        assert normalize_expungement(None) is None

    def test_texas_expunction_eligible_now(self):
        """When TX expunction is eligible now, returns that inner result."""
        exp = ExpungementResult(
            eligibility=ExpungementEligibility.ELIGIBLE_NOW,
            years_remaining=0,
            steps=["File petition for expunction"],
            filing_fee="$280",
        )
        tx = TexasRecordClearingResult(
            expunction_eligible=True,
            expunction_result=exp,
            nondisclosure_eligible=False,
        )
        normalized = normalize_expungement(tx)
        assert isinstance(normalized, ExpungementResult)
        assert normalized.eligibility == ExpungementEligibility.ELIGIBLE_NOW
        assert normalized.filing_fee == "$280"

    def test_texas_nondisclosure_eligible_now_preferred_over_expunction_future(self):
        """Nondisclosure-now beats expunction-future."""
        exp = ExpungementResult(
            eligibility=ExpungementEligibility.ELIGIBLE_FUTURE,
            years_remaining=3,
        )
        nond = ExpungementResult(
            eligibility=ExpungementEligibility.ELIGIBLE_NOW,
            years_remaining=0,
            steps=["File nondisclosure petition"],
            filing_fee="$280",
        )
        tx = TexasRecordClearingResult(
            expunction_eligible=False,
            expunction_result=exp,
            nondisclosure_eligible=True,
            nondisclosure_result=nond,
        )
        normalized = normalize_expungement(tx)
        assert normalized is nond

    def test_texas_both_future_prefers_expunction(self):
        """When both are future-eligible, expunction is preferred."""
        exp = ExpungementResult(
            eligibility=ExpungementEligibility.ELIGIBLE_FUTURE,
            years_remaining=2,
            notes="Expunction path",
        )
        nond = ExpungementResult(
            eligibility=ExpungementEligibility.ELIGIBLE_FUTURE,
            years_remaining=5,
            notes="Nondisclosure path",
        )
        tx = TexasRecordClearingResult(
            expunction_result=exp,
            nondisclosure_result=nond,
        )
        normalized = normalize_expungement(tx)
        assert normalized is exp

    def test_texas_both_not_eligible_returns_expunction(self):
        """Fallback: returns expunction result even when neither eligible."""
        exp = ExpungementResult(
            eligibility=ExpungementEligibility.NOT_ELIGIBLE,
            notes="Not eligible for expunction.",
        )
        nond = ExpungementResult(
            eligibility=ExpungementEligibility.NOT_ELIGIBLE,
            notes="Not eligible for nondisclosure.",
        )
        tx = TexasRecordClearingResult(
            expunction_result=exp,
            nondisclosure_result=nond,
        )
        normalized = normalize_expungement(tx)
        assert normalized is exp

    def test_normalized_result_fits_barrier_card(self):
        """Normalized TX result stores cleanly in BarrierCard.expungement."""
        exp = ExpungementResult(
            eligibility=ExpungementEligibility.ELIGIBLE_NOW,
            years_remaining=0,
            steps=["File petition"],
            filing_fee="$280",
        )
        tx = TexasRecordClearingResult(
            expunction_eligible=True,
            expunction_result=exp,
        )
        normalized = normalize_expungement(tx)
        card = BarrierCard(
            type=BarrierType.CRIMINAL_RECORD,
            severity=BarrierSeverity.HIGH,
            title="Record & Legal Support",
            actions=["Contact legal aid"],
            expungement=normalized,
        )
        assert card.expungement is not None
        assert card.expungement.eligibility == ExpungementEligibility.ELIGIBLE_NOW
        assert card.expungement.filing_fee == "$280"


# ── Part 2: BarrierCard type stays clean ───────────────────────────


class TestBarrierCardExpungement:
    """BarrierCard.expungement stays Optional[ExpungementResult]."""

    def test_accepts_expungement_result(self):
        result = ExpungementResult(
            eligibility=ExpungementEligibility.ELIGIBLE_NOW,
        )
        card = BarrierCard(
            type=BarrierType.CRIMINAL_RECORD,
            severity=BarrierSeverity.HIGH,
            title="Record",
            actions=["a"],
            expungement=result,
        )
        assert card.expungement is not None

    def test_accepts_none(self):
        card = BarrierCard(
            type=BarrierType.CREDIT,
            severity=BarrierSeverity.LOW,
            title="Credit",
            actions=["a"],
            expungement=None,
        )
        assert card.expungement is None


# ── Part 3: ZIP validation accepts all configured cities ───────────


class TestZipValidationAgnostic:
    """ZIP validator should accept ZIPs from ANY configured city."""

    def test_accepts_fort_worth_zip(self):
        """76102 is a valid Fort Worth ZIP."""
        from app.modules.matching.zip_validation import is_valid_zip_for_any_city

        assert is_valid_zip_for_any_city("76102") is True

    def test_accepts_montgomery_zip(self):
        """36104 is a valid Montgomery ZIP."""
        from app.modules.matching.zip_validation import is_valid_zip_for_any_city

        assert is_valid_zip_for_any_city("36104") is True

    def test_rejects_unknown_zip(self):
        """90210 (Beverly Hills) is not a configured city."""
        from app.modules.matching.zip_validation import is_valid_zip_for_any_city

        assert is_valid_zip_for_any_city("90210") is False

    def test_rejects_malformed_zip(self):
        """Non-5-digit strings should fail."""
        from app.modules.matching.zip_validation import is_valid_zip_for_any_city

        assert is_valid_zip_for_any_city("abc") is False
        assert is_valid_zip_for_any_city("1234") is False


# ── Part 4: ZIP → city resolution ─────────────────────────────────


class TestZipCityResolution:
    """resolve_city_for_zip returns the correct city slug from a ZIP."""

    def test_resolves_fort_worth_from_zip(self):
        from app.modules.matching.zip_validation import resolve_city_for_zip

        assert resolve_city_for_zip("76102") == "fort-worth"

    def test_resolves_montgomery_from_zip(self):
        from app.modules.matching.zip_validation import resolve_city_for_zip

        assert resolve_city_for_zip("36104") == "montgomery"

    def test_returns_none_for_unknown_zip(self):
        from app.modules.matching.zip_validation import resolve_city_for_zip

        assert resolve_city_for_zip("90210") is None


# ── Part 5: City context var for per-request routing ───────────────


class TestCityContextVar:
    """The city context var lets downstream code resolve the request's city."""

    @pytest.fixture(autouse=True)
    def _clean_context(self):
        """Ensure city context is clean before and after each test."""
        from app.cities.config import clear_city_context

        clear_city_context()
        yield
        clear_city_context()

    def test_set_and_get_city_context(self):
        from app.cities.config import get_city_config, set_city_context

        set_city_context("montgomery")
        config = get_city_config()
        assert config.state == "AL"
        assert config.name == "Montgomery"

    def test_set_fort_worth_context(self):
        from app.cities.config import get_city_config, set_city_context

        set_city_context("fort-worth")
        config = get_city_config()
        assert config.state == "TX"
        assert config.name == "Fort Worth"

    def test_default_falls_back_to_settings(self):
        """Without context var, get_city_config uses the settings default."""
        from app.cities.config import get_city_config, load_city_config
        from app.core.config import get_settings

        default_city = get_settings().city
        config = get_city_config()
        assert config == load_city_config(default_city)

    def test_context_clears_properly(self):
        from app.cities.config import (
            clear_city_context,
            get_city_config,
            load_city_config,
            set_city_context,
        )
        from app.core.config import get_settings

        set_city_context("montgomery")
        assert get_city_config().state == "AL"

        clear_city_context()
        default_city = get_settings().city
        assert get_city_config() == load_city_config(default_city)


# ── Part 6: _legal_aid_action is city-aware ──────────────────────────


class TestLegalAidActionCityAware:
    """_legal_aid_action() must return city-appropriate legal aid info."""

    @pytest.fixture(autouse=True)
    def _clean_context(self):
        from app.cities.config import clear_city_context

        clear_city_context()
        yield
        clear_city_context()

    def test_alabama_context_returns_legal_services_alabama(self):
        from app.cities.config import set_city_context
        from app.modules.plan.generators_barriers import _legal_aid_action

        set_city_context("montgomery")
        _phase, action = _legal_aid_action()
        assert "Legal Services Alabama" in action.title
        assert "1-866-456-4995" in action.detail
        assert action.resource_name == "Legal Services Alabama"
        assert action.resource_phone == "1-866-456-4995"

    def test_texas_context_returns_legal_aid_nw_texas(self):
        from app.cities.config import set_city_context
        from app.modules.plan.generators_barriers import _legal_aid_action

        set_city_context("fort-worth")
        _phase, action = _legal_aid_action()
        assert "Legal Aid of NorthWest Texas" in action.title
        assert "817-336-3943" in action.detail
        assert action.resource_name == "Legal Aid of NorthWest Texas"
        assert action.resource_phone == "817-336-3943"

    def test_default_context_returns_valid_action(self):
        """Without explicit context, falls back to server default city."""
        from app.modules.plan.generators_barriers import _legal_aid_action

        _phase, action = _legal_aid_action()
        # Should return SOME legal aid info (the server default's)
        assert action.resource_name is not None
        assert action.resource_phone is not None
