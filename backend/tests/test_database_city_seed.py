"""Tests verifying database seeding uses city-aware data_dir and seed file map."""

from pathlib import Path
from unittest.mock import patch

from app.cities.config import CityConfig
from app.core.database import _seed_file_map, resolve_data_dir


def _fw_config():
    return CityConfig(
        name="Fort Worth", state="TX", location="Fort Worth, TX",
        zip_ranges=["76101-76199"], job_adapters=["twc"],
        data_dir="data/cities/fort-worth",
    )


class TestResolveDataDir:
    """Verify resolve_data_dir respects city config."""

    def test_resolve_data_dir_uses_city_data_dir(self):
        """When city config has data_dir, resolve_data_dir should use it."""
        with patch("app.core.database.get_city_config", return_value=_fw_config()):
            data_dir = resolve_data_dir()
            # Should contain "fort-worth" in the path
            assert "fort-worth" in str(data_dir)


class TestSeedFileMap:
    """Verify seed file map is city-agnostic."""

    def test_no_montgomery_in_seed_filenames(self):
        """Seed file map must not contain 'montgomery' in filenames."""
        for filename, table in _seed_file_map():
            assert "montgomery" not in filename.lower(), (
                f"Seed file '{filename}' contains 'montgomery'. "
                "Use city-agnostic filenames."
            )
