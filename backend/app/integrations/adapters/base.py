"""JobAdapter protocol and adapter registry with lazy imports."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class JobAdapter(Protocol):
    async def fetch_jobs(
        self, session, query: str, location: str
    ) -> list[dict]: ...


class AdapterNotFoundError(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"No adapter registered for '{name}'")
        self.adapter_name = name


_ADAPTER_REGISTRY: dict[str, str] = {
    "brightdata": "app.integrations.adapters.brightdata_adapter:BrightDataJobAdapter",
    "twc": "app.integrations.adapters.twc_adapter:TWCJobAdapter",
    "usajobs": "app.integrations.adapters.usajobs_adapter:USAJobsJobAdapter",
}


def get_adapter(name: str) -> JobAdapter:
    path = _ADAPTER_REGISTRY.get(name)
    if path is None:
        raise AdapterNotFoundError(name)
    module_path, class_name = path.rsplit(":", 1)
    import importlib

    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    return cls()
