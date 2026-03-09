"""Tests for findhelp.org capability URL generation."""

import pytest

from app.modules.matching.types import BarrierType
from app.modules.resources.findhelp import (
    FINDHELP_CATEGORIES,
    generate_findhelp_url,
)


class TestFindhelpCategories:
    """Verify every barrier type has a findhelp category mapping."""

    def test_all_barrier_types_mapped(self) -> None:
        """Every BarrierType must have a findhelp category."""
        for bt in BarrierType:
            assert bt in FINDHELP_CATEGORIES, f"Missing mapping for {bt}"

    def test_no_extra_mappings(self) -> None:
        """No stale mappings for barrier types that don't exist."""
        for key in FINDHELP_CATEGORIES:
            assert key in list(BarrierType), f"Stale mapping: {key}"


class TestGenerateFindhelpUrl:
    """Test URL generation for each barrier type."""

    @pytest.mark.parametrize("barrier", list(BarrierType))
    def test_url_contains_base_domain(self, barrier: str) -> None:
        url = generate_findhelp_url(barrier, "36104")
        assert url is not None
        assert url.startswith("https://www.findhelp.org/")

    @pytest.mark.parametrize("barrier", list(BarrierType))
    def test_url_contains_zip_code(self, barrier: str) -> None:
        url = generate_findhelp_url(barrier, "36104")
        assert url is not None
        assert "postal=36104" in url

    def test_credit_url(self) -> None:
        url = generate_findhelp_url(BarrierType.CREDIT, "36101")
        assert url is not None
        assert "financial-assistance" in url
        assert "postal=36101" in url

    def test_transportation_url(self) -> None:
        url = generate_findhelp_url(BarrierType.TRANSPORTATION, "36104")
        assert url is not None
        assert "transportation" in url

    def test_childcare_url(self) -> None:
        url = generate_findhelp_url(BarrierType.CHILDCARE, "36104")
        assert url is not None
        assert "childcare" in url.lower() or "child-care" in url.lower()

    def test_housing_url(self) -> None:
        url = generate_findhelp_url(BarrierType.HOUSING, "36104")
        assert url is not None
        assert "housing" in url

    def test_health_url(self) -> None:
        url = generate_findhelp_url(BarrierType.HEALTH, "36104")
        assert url is not None
        assert "health" in url

    def test_training_url(self) -> None:
        url = generate_findhelp_url(BarrierType.TRAINING, "36104")
        assert url is not None
        assert "job-training" in url or "training" in url

    def test_criminal_record_url(self) -> None:
        url = generate_findhelp_url(BarrierType.CRIMINAL_RECORD, "36104")
        assert url is not None
        assert "reentry" in url or "formerly-incarcerated" in url

    def test_invalid_barrier_returns_none(self) -> None:
        url = generate_findhelp_url("not_a_barrier", "36104")
        assert url is None

    def test_url_includes_montgomery(self) -> None:
        url = generate_findhelp_url(BarrierType.CREDIT, "36104")
        assert url is not None
        assert "montgomery" in url.lower()

    def test_different_zip_codes(self) -> None:
        url1 = generate_findhelp_url(BarrierType.CREDIT, "36101")
        url2 = generate_findhelp_url(BarrierType.CREDIT, "36117")
        assert url1 is not None and url2 is not None
        assert "36101" in url1
        assert "36117" in url2
        assert url1 != url2

    def test_rejects_malformed_zip(self) -> None:
        """Zip codes with injected params must be rejected."""
        assert generate_findhelp_url(BarrierType.CREDIT, "36104&injected=evil") is None

    def test_rejects_empty_zip(self) -> None:
        assert generate_findhelp_url(BarrierType.CREDIT, "") is None

    def test_rejects_non_numeric_zip(self) -> None:
        assert generate_findhelp_url(BarrierType.CREDIT, "abcde") is None

    def test_rejects_short_zip(self) -> None:
        assert generate_findhelp_url(BarrierType.CREDIT, "361") is None
