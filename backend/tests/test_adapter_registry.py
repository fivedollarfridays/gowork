"""Tests for JobAdapter protocol and adapter registry."""

import pytest


class TestJobAdapterProtocol:
    def test_protocol_has_fetch_jobs_method(self):
        from app.integrations.adapters.base import JobAdapter
        import inspect

        hints = inspect.get_annotations(JobAdapter)
        assert "fetch_jobs" not in hints
        members = [m for m in dir(JobAdapter) if not m.startswith("_")]
        assert "fetch_jobs" in members

    def test_concrete_class_satisfies_protocol(self):
        from app.integrations.adapters.base import JobAdapter
        from typing import Protocol

        assert issubclass(JobAdapter, Protocol)

        class FakeAdapter:
            async def fetch_jobs(self, session, query: str, location: str) -> list[dict]:
                return []

        assert isinstance(FakeAdapter(), JobAdapter)

    def test_non_conforming_class_fails_protocol(self):
        from app.integrations.adapters.base import JobAdapter

        class BadAdapter:
            pass

        assert not isinstance(BadAdapter(), JobAdapter)


class TestAdapterNotFoundError:
    def test_is_exception(self):
        from app.integrations.adapters.base import AdapterNotFoundError

        assert issubclass(AdapterNotFoundError, Exception)

    def test_includes_adapter_name(self):
        from app.integrations.adapters.base import AdapterNotFoundError

        err = AdapterNotFoundError("unknown")
        assert "unknown" in str(err)


class TestGetAdapter:
    def test_unknown_adapter_raises(self):
        from app.integrations.adapters.base import get_adapter, AdapterNotFoundError

        with pytest.raises(AdapterNotFoundError):
            get_adapter("unknown")

    def test_brightdata_adapter_returns_instance(self):
        from app.integrations.adapters.base import get_adapter, JobAdapter

        adapter = get_adapter("brightdata")
        assert isinstance(adapter, JobAdapter)

    def test_no_brightdata_import_at_module_level(self):
        """Registry string refs to brightdata are OK; actual imports are not."""
        import pathlib
        import importlib.util

        spec = importlib.util.find_spec("app.integrations.adapters.base")
        src = pathlib.Path(spec.origin).read_text()

        import_lines = [
            line.strip()
            for line in src.splitlines()
            if (line.strip().startswith("import ") or line.strip().startswith("from "))
            and not line.strip().startswith("#")
        ]
        for line in import_lines:
            assert "brightdata" not in line.lower(), (
                f"Found BrightData import at module level: {line}"
            )

