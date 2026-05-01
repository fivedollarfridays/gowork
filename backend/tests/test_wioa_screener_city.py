"""Tests verifying wioa_screener uses city-aware cert DB."""

import ast
from pathlib import Path


class TestWIOAScreenerCityAware:
    """Verify wioa_screener uses resource_router for cert data."""

    def test_no_direct_cert_db_import_from_filters(self):
        """wioa_screener must not import CERT_DB from filters."""
        source = Path("app/modules/matching/wioa_screener.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if "filters" in node.module:
                    imported_names = [a.name for a in node.names]
                    assert "CERT_DB" not in imported_names, (
                        "wioa_screener must not import CERT_DB from filters. "
                        "Use get_cert_db() from resource_router instead."
                    )

    def test_uses_resource_router_for_cert_db(self):
        """wioa_screener should import from resource_router."""
        source = Path("app/modules/matching/wioa_screener.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if "resource_router" in node.module:
                    imported_names = [a.name for a in node.names]
                    if "get_cert_db" in imported_names:
                        found = True
        assert found, (
            "wioa_screener must import get_cert_db from resource_router"
        )
