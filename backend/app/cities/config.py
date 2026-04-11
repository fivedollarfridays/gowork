"""City configuration schema and YAML loader."""

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel

from app.core.config import _CITY_SLUG_RE

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
    from app.core.config import get_settings

    return load_city_config(get_settings().city)
