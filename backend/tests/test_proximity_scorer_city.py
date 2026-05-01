"""Tests verifying proximity_scorer uses geo_router (city-aware coordinates)."""

from unittest.mock import patch

from app.cities.config import CityConfig


def _fw_config():
    return CityConfig(
        name="Fort Worth", state="TX", location="Fort Worth, TX",
        zip_ranges=["76101-76199"], job_adapters=["twc"],
        data_dir="data/cities/fort-worth",
    )


class TestProximityScorerCityAware:
    """Verify proximity_scorer uses geo_router for coordinates."""

    def test_imports_from_geo_router_not_scoring(self):
        """proximity_scorer must import coords from geo_router, not scoring."""
        import ast
        from pathlib import Path

        source = Path("app/modules/matching/proximity_scorer.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if "scoring" in node.module:
                    imported_names = [a.name for a in node.names]
                    assert "DOWNTOWN_MONTGOMERY" not in imported_names, (
                        "proximity_scorer must not import DOWNTOWN_MONTGOMERY from scoring"
                    )
                    assert "ZIP_CENTROIDS" not in imported_names, (
                        "proximity_scorer must not import ZIP_CENTROIDS from scoring"
                    )

    def test_fort_worth_uses_fw_downtown_coords(self):
        """CITY=fort-worth must use FW downtown, not Montgomery."""
        with patch("app.modules.matching.proximity_scorer.get_downtown_coords") as mock_dt, \
             patch("app.modules.matching.proximity_scorer.get_zip_centroids") as mock_zc:
            mock_dt.return_value = (32.7555, -97.3308)  # Fort Worth
            mock_zc.return_value = {"76101": (32.7555, -97.3308)}

            from app.modules.matching.proximity_scorer import score_proximity
            score = score_proximity("76101", "123 Main St, Fort Worth, TX 76101", False)
            assert score == 1.0  # Same ZIP => 0 distance => max score

            # Verify the router functions were actually called
            mock_dt.assert_called()
            mock_zc.assert_called()

    def test_unknown_zip_uses_city_downtown_not_montgomery(self):
        """Unknown ZIP should fall back to city downtown, not DOWNTOWN_MONTGOMERY."""
        with patch("app.modules.matching.proximity_scorer.get_downtown_coords") as mock_dt, \
             patch("app.modules.matching.proximity_scorer.get_zip_centroids") as mock_zc:
            mock_dt.return_value = (32.7555, -97.3308)  # Fort Worth
            mock_zc.return_value = {}  # Empty centroids

            from app.modules.matching.proximity_scorer import score_proximity
            # Both user and job fall back to downtown => 0 distance => 1.0
            score = score_proximity("99999", "Nowhere, TX 99998", False)
            assert score == 1.0
            mock_dt.assert_called()
