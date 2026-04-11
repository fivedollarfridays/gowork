"""JobAdapter protocol and adapter registry with lazy imports."""

from __future__ import annotations

import importlib
from functools import lru_cache
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@runtime_checkable
class JobAdapter(Protocol):
    async def fetch_jobs(
        self, session: AsyncSession, query: str, location: str
    ) -> list[dict]: ...


class AdapterNotFoundError(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"No adapter registered for '{name}'")
        self.adapter_name = name


_ADAPTER_REGISTRY: dict[str, str] = {
    "brightdata": "app.integrations.adapters.brightdata_adapter:BrightDataJobAdapter",
    "honestjobs": "app.integrations.adapters.honestjobs_adapter:HonestJobsJobAdapter",
    "twc": "app.integrations.adapters.twc_adapter:TWCJobAdapter",
    "usajobs": "app.integrations.adapters.usajobs_adapter:USAJobsJobAdapter",
}


@lru_cache(maxsize=None)
def get_adapter(name: str) -> JobAdapter:
    path = _ADAPTER_REGISTRY.get(name)
    if path is None:
        raise AdapterNotFoundError(name)
    module_path, class_name = path.rsplit(":", 1)
    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    return cls()
