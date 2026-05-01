"""City configuration schema and YAML loader."""

from contextvars import ContextVar
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel

from app.core.config import _CITY_SLUG_RE

# Per-request city override — set by the assessment route after
# resolving the city from the user's ZIP code.  When set, get_city_config()
# returns THIS city's config instead of the server default.
_city_context: ContextVar[str | None] = ContextVar("_city_context", default=None)

CITIES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "cities"


class CityConfigNotFoundError(FileNotFoundError):
    pass


class CityConfig(BaseModel):
    name: str
    state: str
    location: str
    zip_ranges: list[str]
    job_adapters: list[str]
    data_dir: str


@lru_cache(maxsize=None)
def load_city_config(city: str) -> CityConfig:
    if not _CITY_SLUG_RE.match(city):
        raise CityConfigNotFoundError(f"City config not found: {city!r}")
    resolved_cities_dir = CITIES_DIR.resolve()
    path = (resolved_cities_dir / f"{city}.yaml").resolve()
    if not path.is_relative_to(resolved_cities_dir) or not path.exists():
        raise CityConfigNotFoundError(f"City config not found: {city!r}")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise CityConfigNotFoundError(f"City config not found: {city!r}")
    return CityConfig(**data)


def get_city_config() -> CityConfig:
    """Return the active city config.

    Checks the per-request context var first (set via ``set_city_context``),
    falling back to the server-level ``settings.city`` default.
    """
    ctx_city = _city_context.get()
    if ctx_city is not None:
        return load_city_config(ctx_city)
    from app.core.config import get_settings

    return load_city_config(get_settings().city)


def set_city_context(city_slug: str) -> None:
    """Set the per-request city override (call from assessment route)."""
    _city_context.set(city_slug)


def clear_city_context() -> None:
    """Clear the per-request city override."""
    _city_context.set(None)
