"""Tests verifying barrier_cards.py uses criminal router for record clearing."""

import ast
from pathlib import Path


class TestBarrierCardsUsesRouter:
    """Verify barrier_cards imports from criminal.router, not expungement directly."""

    def test_no_direct_expungement_import(self):
        """barrier_cards must not import check_expungement_eligibility from expungement."""
        source = Path("app/modules/matching/barrier_cards.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if "expungement" in node.module:
                    imported_names = [a.name for a in node.names]
                    assert "check_expungement_eligibility" not in imported_names, (
                        "barrier_cards must not import check_expungement_eligibility "
                        "directly from expungement. Use criminal.router instead."
                    )

    def test_imports_from_criminal_router(self):
        """barrier_cards must import check_record_clearing from criminal.router."""
        source = Path("app/modules/matching/barrier_cards.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if "criminal.router" in node.module:
                    imported_names = [a.name for a in node.names]
                    if "check_record_clearing" in imported_names:
                        found = True
        assert found, (
            "barrier_cards must import check_record_clearing from criminal.router"
        )
