"""Integration tests: CITY=fort-worth produces correct city-specific output.

Verifies that the full Fort Worth flow does not leak Montgomery/Alabama data.
"""

import pytest
from unittest.mock import patch

from app.cities.config import CityConfig, load_city_config
from app.core.config import get_settings
from app.modules.matching.types import BarrierType, BarrierSeverity, EmploymentStatus, UserProfile


def _fw_config():
    return CityConfig(
        name="Fort Worth", state="TX", location="Fort Worth, TX",
        zip_ranges=["76101-76199"], job_adapters=["twc"],
        data_dir="data/cities/fort-worth",
    )


@pytest.fixture(autouse=True)
def _clear_caches():
    """Clear LRU caches between tests."""
    load_city_config.cache_clear()
    get_settings.cache_clear()
    yield
    load_city_config.cache_clear()
    get_settings.cache_clear()


def _patch_city_config():
    """Return a context manager that patches get_city_config everywhere it's used."""
    fw = _fw_config()
    # Patch at the definition site so all importers see it
    return patch("app.cities.config.get_city_config", return_value=fw)


class TestFortWorthProximityScoring:
    """Integration: Fort Worth proximity uses FW coordinates."""

    def test_proximity_score_uses_fw_downtown(self):
        """Fort Worth ZIP proximity should use FW downtown, not Montgomery."""
        with _patch_city_config(), \
             patch("app.modules.matching.geo_router.get_city_config", return_value=_fw_config()):
            from app.modules.matching.proximity_scorer import score_proximity
            score = score_proximity("76101", "123 Main St, Fort Worth, TX 76101", False)
            assert score == 1.0

    def test_fw_zip_centroids_used(self):
        """FW ZIP centroids should have Fort Worth ZIPs, not Montgomery ZIPs."""
        with _patch_city_config(), \
             patch("app.modules.matching.geo_router.get_city_config", return_value=_fw_config()):
            from app.modules.matching.geo_router import get_zip_centroids
            centroids = get_zip_centroids()
            assert "76101" in centroids
            assert "76102" in centroids
            assert "36101" not in centroids
            assert "36104" not in centroids


class TestFortWorthBarrierCards:
    """Integration: Fort Worth barrier cards use TX criminal rules."""

    def test_criminal_barrier_uses_tx_expunction(self):
        """Fort Worth criminal barrier should route to Texas expunction."""
        with _patch_city_config(), \
             patch("app.modules.criminal.router.get_city_config", return_value=_fw_config()):
            from app.modules.criminal.router import check_record_clearing
            result = check_record_clearing(None)
            assert hasattr(result, "expunction_eligible") or hasattr(result, "nondisclosure_eligible"), (
                "Fort Worth should get Texas record clearing, not Alabama expungement"
            )


class TestFortWorthResources:
    """Integration: Fort Worth resources are city-specific."""

    def test_barrier_actions_are_tx_specific(self):
        """Fort Worth barrier actions should reference TX resources."""
        with _patch_city_config(), \
             patch("app.modules.matching.resource_router.get_city_config", return_value=_fw_config()):
            from app.modules.matching.resource_router import get_barrier_actions
            actions = get_barrier_actions()
            transport_actions = actions.get(BarrierType.TRANSPORTATION, [])
            combined = " ".join(transport_actions)
            assert "Trinity Metro" in combined
            assert "M-Transit" not in combined

    def test_career_center_is_workforce_solutions(self):
        """Fort Worth career center should be Workforce Solutions."""
        with _patch_city_config(), \
             patch("app.modules.matching.resource_router.get_city_config", return_value=_fw_config()):
            from app.modules.matching.resource_router import get_career_center
            center = get_career_center()
            assert "Workforce Solutions" in center.name
            assert "Montgomery" not in center.name

    def test_cert_db_is_tx_specific(self):
        """Fort Worth cert DB should reference Texas Board of Nursing."""
        with _patch_city_config(), \
             patch("app.modules.matching.resource_router.get_city_config", return_value=_fw_config()):
            from app.modules.matching.resource_router import get_cert_db
            cert_db = get_cert_db()
            cna = cert_db.get("CNA", {})
            body = cna.get("renewal_body", {})
            assert "Texas" in body.get("name", "")
            assert "Alabama" not in body.get("name", "")


class TestFortWorthPrecrawl:
    """Integration: Precrawl uses Fort Worth location."""

    def test_keyword_searches_use_fw_location(self):
        """Precrawl keyword searches should target Fort Worth, TX."""
        with _patch_city_config(), \
             patch("app.integrations.brightdata.precrawl.get_city_config", return_value=_fw_config()):
            from app.integrations.brightdata.precrawl import build_keyword_searches
            searches = build_keyword_searches()
            for s in searches:
                assert s["location"] == "Fort Worth, TX"
                assert s["location"] != "Montgomery, AL"


class TestFortWorthFilters:
    """Integration: Filters use city-aware ZIP ranges."""

    def test_childcare_filter_fw_zips(self):
        """Fort Worth childcare filter should include FW ZIP area."""
        from app.modules.matching.types import Resource

        with _patch_city_config(), \
             patch("app.modules.matching.filters.get_city_config", return_value=_fw_config()):
            from app.modules.matching.filters import apply_childcare_filter
            resources = [
                Resource(id=1, name="FW Day Care", category="childcare",
                         address="100 Main St, Fort Worth, TX 76102"),
                Resource(id=2, name="AL Day Care", category="childcare",
                         address="200 Oak St, Montgomery, AL 36104"),
            ]
            result = apply_childcare_filter(resources, "76101", ["76102"])
            names = [r.name for r in result]
            assert "FW Day Care" in names
            assert "AL Day Care" not in names


class TestNoMontgomeryLeaksInFortWorth:
    """Integration: Full scan for Montgomery/Alabama leaks in FW mode."""

    def test_barrier_intel_prompt_uses_fw(self):
        """Barrier intel prompt should reference Fort Worth."""
        with _patch_city_config(), \
             patch("app.barrier_intel.prompts.get_city_config", return_value=_fw_config()):
            from app.barrier_intel.prompts import get_barrier_intel_system_prompt
            prompt = get_barrier_intel_system_prompt()
            assert "Fort Worth" in prompt
            assert "Montgomery" not in prompt

    def test_hallucination_disclaimer_uses_fw(self):
        """Hallucination disclaimer should reference Tarrant County."""
        with _patch_city_config():
            from app.barrier_intel.guardrails import _get_hallucination_disclaimer
            disclaimer = _get_hallucination_disclaimer()
            assert "Tarrant County" in disclaimer or "Workforce Solutions" in disclaimer
            assert "Alabama Career Center" not in disclaimer
