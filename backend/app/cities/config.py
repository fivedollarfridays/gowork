"""City configuration schema and YAML loader."""

from pathlib import Path

import yaml
from pydantic import BaseModel

CITIES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "cities"


class CityConfigNotFoundError(FileNotFoundError):
    pass


class CityConfig(BaseModel):
    name: str
    state: str
    zip_ranges: list[str]
    job_adapters: list[str]
    data_dir: str


def load_city_config(city: str) -> CityConfig:
    path = CITIES_DIR / f"{city}.yaml"
    if not path.exists():
        raise CityConfigNotFoundError(
            f"City config not found: {city} (expected {path})"
        )
    with open(path) as f:
        data = yaml.safe_load(f)
    return CityConfig(**data)


def get_city_config() -> CityConfig:
    from app.core.config import get_settings

    return load_city_config(get_settings().city)
