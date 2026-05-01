"""Tests verifying precrawl.py uses city config for location."""

import ast
from pathlib import Path
from unittest.mock import patch

from app.cities.config import CityConfig


def _fw_config():
    return CityConfig(
        name="Fort Worth", state="TX", location="Fort Worth, TX",
        zip_ranges=["76101-76199"], job_adapters=["twc"],
        data_dir="data/cities/fort-worth",
    )


class TestPrecrawlCityAware:
    """Verify precrawl uses city config location, not hardcoded Montgomery."""

    def test_no_hardcoded_montgomery_location(self):
        """precrawl.py must not have _LOCATION = 'Montgomery, AL'."""
        source = Path("app/integrations/brightdata/precrawl.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "_LOCATION":
                        assert False, (
                            "precrawl.py must not have hardcoded _LOCATION. "
                            "Use get_city_config().location instead."
                        )

    def test_function_not_named_precrawl_montgomery(self):
        """Function should be named precrawl_jobs, not precrawl_montgomery_jobs."""
        source = Path("app/integrations/brightdata/precrawl.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                assert "montgomery" not in node.name.lower(), (
                    f"Function '{node.name}' contains 'montgomery' in its name. "
                    "Rename to city-agnostic name."
                )

    def test_build_search_urls_uses_city_location(self):
        """build_search_urls should use the city config location."""
        with patch("app.integrations.brightdata.precrawl.get_city_config", return_value=_fw_config()):
            from app.integrations.brightdata.precrawl import build_search_urls
            urls = build_search_urls()
            assert len(urls) > 0
            for url in urls:
                assert "Montgomery" not in url
                assert "Fort+Worth" in url or "Fort%2BWorth" in url or "Fort" in url

    def test_build_keyword_searches_uses_city_location(self):
        """build_keyword_searches should use city config location."""
        with patch("app.integrations.brightdata.precrawl.get_city_config", return_value=_fw_config()):
            from app.integrations.brightdata.precrawl import build_keyword_searches
            searches = build_keyword_searches()
            assert len(searches) > 0
            for s in searches:
                assert s["location"] != "Montgomery, AL"
                assert s["location"] == "Fort Worth, TX"
