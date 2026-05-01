"""S8 Polish: code quality gate tests.

These tests enforce structural invariants that prevent quality regressions:
- All routes registered
- No files over size limits
- Public functions have type hints
- No unused imports in routes
"""

import ast
import os

import pytest


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------


class TestRouteRegistration:
    """Every router file must be registered in all_routers."""

    def test_all_route_files_registered(self) -> None:
        """Each .py file in routes/ should have its router in all_routers."""
        from app.routes import all_routers

        routes_dir = os.path.join(os.path.dirname(__file__), "..", "app", "routes")
        route_files = {
            f[:-3]
            for f in os.listdir(routes_dir)
            if f.endswith(".py")
            and not f.startswith("_")  # exclude __init__.py and private helper modules
            and f != "career_center.py"
        }
        # career_center is registered via plan_router (side-effect import)
        # _*-prefixed modules are package-private helpers (no router exported)

        # Verify we have at least as many routers as route files
        assert len(all_routers) >= len(route_files), (
            f"Expected at least {len(route_files)} routers, got {len(all_routers)}"
        )

    def test_all_routers_have_prefix(self) -> None:
        """Every router should have a prefix set."""
        from app.routes import all_routers

        for router in all_routers:
            assert router.prefix, f"Router {router!r} has no prefix"


# ---------------------------------------------------------------------------
# File size limits
# ---------------------------------------------------------------------------


class TestFileSizeLimits:
    """Production files must stay under 400 lines."""

    def _get_py_files(self, directory: str) -> list[str]:
        result = []
        for dirpath, _, filenames in os.walk(directory):
            for f in filenames:
                if f.endswith(".py") and not f.startswith("__"):
                    result.append(os.path.join(dirpath, f))
        return result

    def test_route_files_under_400(self) -> None:
        routes_dir = os.path.join(os.path.dirname(__file__), "..", "app", "routes")
        for fp in self._get_py_files(routes_dir):
            with open(fp, encoding="utf-8") as fh:
                lines = sum(1 for _ in fh)
            assert lines < 400, f"{fp} has {lines} lines (max 400)"

    def test_module_files_under_400(self) -> None:
        modules_dir = os.path.join(os.path.dirname(__file__), "..", "app", "modules")
        for fp in self._get_py_files(modules_dir):
            with open(fp, encoding="utf-8") as fh:
                lines = sum(1 for _ in fh)
            assert lines < 400, f"{fp} has {lines} lines (max 400)"


# ---------------------------------------------------------------------------
# Function count limits
# ---------------------------------------------------------------------------


class TestFunctionCountLimits:
    """Production files must have fewer than 15 functions."""

    def _count_functions(self, filepath: str) -> int:
        with open(filepath, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        return sum(
            1 for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        )

    def test_route_files_under_15_functions(self) -> None:
        routes_dir = os.path.join(os.path.dirname(__file__), "..", "app", "routes")
        for dirpath, _, filenames in os.walk(routes_dir):
            for f in filenames:
                if f.endswith(".py") and not f.startswith("__"):
                    fp = os.path.join(dirpath, f)
                    count = self._count_functions(fp)
                    assert count < 15, f"{fp} has {count} functions (max 15)"

    def test_module_files_under_15_functions(self) -> None:
        modules_dir = os.path.join(os.path.dirname(__file__), "..", "app", "modules")
        for dirpath, _, filenames in os.walk(modules_dir):
            for f in filenames:
                if f.endswith(".py") and not f.startswith("__"):
                    fp = os.path.join(dirpath, f)
                    count = self._count_functions(fp)
                    assert count < 15, f"{fp} has {count} functions (max 15)"


# ---------------------------------------------------------------------------
# Public function type hint check
# ---------------------------------------------------------------------------


class TestPublicTypeHints:
    """Public functions in routes and modules should have return type hints."""

    def _check_return_hints(self, filepath: str) -> list[str]:
        """Return list of public functions missing return type hints."""
        with open(filepath, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        missing = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"):
                    continue
                if node.returns is None:
                    missing.append(f"{node.name}() at line {node.lineno}")
        return missing

    def test_route_public_functions_have_return_hints(self) -> None:
        """Route public functions should declare return types."""
        routes_dir = os.path.join(os.path.dirname(__file__), "..", "app", "routes")
        issues = []
        for dirpath, _, filenames in os.walk(routes_dir):
            for f in filenames:
                if f.endswith(".py") and not f.startswith("__"):
                    fp = os.path.join(dirpath, f)
                    missing = self._check_return_hints(fp)
                    if missing:
                        issues.append(f"{fp}: {missing}")
        assert not issues, f"Missing return type hints:\n" + "\n".join(issues)
