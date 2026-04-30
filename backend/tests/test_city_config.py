"""Tests for CityConfig schema and YAML loader."""

import pytest
import yaml
from pydantic import ValidationError

from pathlib import Path

from app.cities.config import (
    CityConfig,
    CityConfigNotFoundError,
    get_city_config,
    load_city_config,
)
from app.core.config import Settings, get_settings


CITIES_DIR = Path(__file__).resolve().parent.parent.parent / "cities"


class TestCityConfigModel:
    def test_valid_config(self):
        cfg = CityConfig(
            name="Montgomery",
            state="AL",
            location="Montgomery, AL",
            zip_ranges=["36101-36120"],
            job_adapters=["brightdata"],
            data_dir="data/montgomery",
        )
        assert cfg.name == "Montgomery"
        assert cfg.state == "AL"
        assert cfg.location == "Montgomery, AL"
        assert cfg.zip_ranges == ["36101-36120"]
        assert cfg.job_adapters == ["brightdata"]
        assert cfg.data_dir == "data/montgomery"

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            CityConfig(
                state="AL",
                location="Montgomery, AL",
                zip_ranges=["36101"],
                job_adapters=["brightdata"],
                data_dir="data/montgomery",
            )

    def test_missing_state_raises(self):
        with pytest.raises(ValidationError):
            CityConfig(
                name="Montgomery",
                location="Montgomery, AL",
                zip_ranges=["36101"],
                job_adapters=["brightdata"],
                data_dir="data/montgomery",
            )

    def test_missing_location_raises(self):
        with pytest.raises(ValidationError):
            CityConfig(
                name="Montgomery",
                state="AL",
                zip_ranges=["36101"],
                job_adapters=["brightdata"],
                data_dir="data/montgomery",
            )

    def test_missing_zip_ranges_raises(self):
        with pytest.raises(ValidationError):
            CityConfig(
                name="Montgomery",
                state="AL",
                location="Montgomery, AL",
                job_adapters=["brightdata"],
                data_dir="data/montgomery",
            )

    def test_missing_job_adapters_raises(self):
        with pytest.raises(ValidationError):
            CityConfig(
                name="Montgomery",
                state="AL",
                location="Montgomery, AL",
                zip_ranges=["36101"],
                data_dir="data/montgomery",
            )

    def test_missing_data_dir_raises(self):
        with pytest.raises(ValidationError):
            CityConfig(
                name="Montgomery",
                state="AL",
                location="Montgomery, AL",
                zip_ranges=["36101"],
                job_adapters=["brightdata"],
            )

    def test_zip_ranges_must_be_list(self):
        with pytest.raises(ValidationError):
            CityConfig(
                name="Montgomery",
                state="AL",
                location="Montgomery, AL",
                zip_ranges="36101",
                job_adapters=["brightdata"],
                data_dir="data/montgomery",
            )

    def test_job_adapters_must_be_list(self):
        with pytest.raises(ValidationError):
            CityConfig(
                name="Montgomery",
                state="AL",
                location="Montgomery, AL",
                zip_ranges=["36101"],
                job_adapters="brightdata",
                data_dir="data/montgomery",
            )


class TestLoadCityConfig:
    def test_load_montgomery(self):
        cfg = load_city_config("montgomery")
        assert cfg.name == "Montgomery"
        assert cfg.state == "AL"
        assert len(cfg.zip_ranges) > 0
        assert len(cfg.job_adapters) > 0
        assert cfg.data_dir

    def test_load_fort_worth(self):
        cfg = load_city_config("fort-worth")
        assert cfg.name == "Fort Worth"
        assert cfg.state == "TX"
        assert len(cfg.zip_ranges) > 0
        assert len(cfg.job_adapters) > 0

    def test_load_nonexistent_raises(self):
        with pytest.raises(CityConfigNotFoundError, match="nonexistent"):
            load_city_config("nonexistent")

    def test_error_message_includes_city_name(self):
        with pytest.raises(CityConfigNotFoundError) as exc_info:
            load_city_config("atlantis")
        assert "atlantis" in str(exc_info.value)

    def test_loaded_config_matches_yaml(self):
        cfg = load_city_config("montgomery")
        yaml_path = CITIES_DIR / "montgomery.yaml"
        with open(yaml_path) as f:
            raw = yaml.safe_load(f)
        assert cfg.name == raw["name"]
        assert cfg.state == raw["state"]
        assert cfg.zip_ranges == raw["zip_ranges"]


class TestCitySettingInConfig:
    def test_default_city_is_fort_worth(self, monkeypatch):
        # Reference deployment is Fort Worth (HackFW). The bare default
        # (no CITY env var, no _env_file) returns "fort-worth"; legacy
        # Montgomery deployments must set CITY=montgomery explicitly.
        monkeypatch.delenv("CITY", raising=False)
        s = Settings(
            _env_file=None,
            anthropic_api_key="test",
        )
        assert s.city == "fort-worth"

    def test_city_can_be_overridden(self):
        s = Settings(
            _env_file=None,
            city="fort-worth",
            anthropic_api_key="test",
        )
        assert s.city == "fort-worth"

    def test_existing_settings_unchanged(self):
        s = Settings(
            _env_file=None,
            anthropic_api_key="test",
        )
        assert s.app_name == "MontGoWork"


class TestMontgomeryYaml:
    def test_validates_against_schema(self):
        cfg = load_city_config("montgomery")
        assert cfg.name == "Montgomery"
        assert cfg.state == "AL"

    def test_has_location(self):
        cfg = load_city_config("montgomery")
        assert cfg.location == "Montgomery, AL"

    def test_has_expected_adapters(self):
        cfg = load_city_config("montgomery")
        assert cfg.job_adapters == ["brightdata", "honestjobs"]

    def test_has_zip_ranges(self):
        cfg = load_city_config("montgomery")
        assert len(cfg.zip_ranges) >= 3
        assert any("36101" in z for z in cfg.zip_ranges)

    def test_data_dir_points_to_cities_subdir(self):
        cfg = load_city_config("montgomery")
        assert cfg.data_dir == "data/cities/montgomery"


class TestFortWorthYaml:
    def test_validates_against_schema(self):
        cfg = load_city_config("fort-worth")
        assert cfg.name == "Fort Worth"
        assert cfg.state == "TX"

    def test_has_expected_adapters(self):
        cfg = load_city_config("fort-worth")
        assert cfg.job_adapters == ["twc", "usajobs"]

    def test_has_zip_ranges(self):
        cfg = load_city_config("fort-worth")
        assert len(cfg.zip_ranges) >= 1
        assert any("76" in z for z in cfg.zip_ranges)

    def test_data_dir_points_to_cities_subdir(self):
        cfg = load_city_config("fort-worth")
        assert cfg.data_dir == "data/cities/fort-worth"


class TestDataDirectories:
    def test_montgomery_data_dir_has_gitkeep(self):
        gitkeep = Path(__file__).resolve().parent.parent.parent / "data" / "cities" / "montgomery" / ".gitkeep"
        assert gitkeep.exists()

    def test_fort_worth_data_dir_has_gitkeep(self):
        gitkeep = Path(__file__).resolve().parent.parent.parent / "data" / "cities" / "fort-worth" / ".gitkeep"
        assert gitkeep.exists()


class TestLoadCityConfigTraversalGuard:
    def test_rejects_dot_dot_traversal(self):
        with pytest.raises(CityConfigNotFoundError):
            load_city_config("../etc/passwd")

    def test_rejects_backslash_traversal(self):
        with pytest.raises(CityConfigNotFoundError):
            load_city_config("..\\windows\\system32")

    def test_rejects_absolute_path(self):
        with pytest.raises(CityConfigNotFoundError):
            load_city_config("/etc/passwd")

    def test_rejects_uppercase(self):
        with pytest.raises(CityConfigNotFoundError):
            load_city_config("Montgomery")

    def test_rejects_null_byte(self):
        with pytest.raises(CityConfigNotFoundError):
            load_city_config("montgomery\x00")

    def test_error_message_does_not_leak_filesystem_path(self):
        with pytest.raises(CityConfigNotFoundError) as exc_info:
            load_city_config("nonexistent-city")
        msg = str(exc_info.value)
        assert "/Users/" not in msg
        assert "/home/" not in msg
        assert str(Path(__file__).resolve().parent.parent.parent) not in msg


class TestGetCityConfig:
    def test_returns_config_for_default_city(self, monkeypatch):
        # Bare default (no CITY env var) is now Fort Worth — the active
        # reference deployment. Legacy Montgomery loads remain available
        # via explicit CITY=montgomery.
        monkeypatch.delenv("CITY", raising=False)
        get_settings.cache_clear()
        try:
            cfg = get_city_config()
            assert cfg.name == "Fort Worth"
        finally:
            get_settings.cache_clear()

    def test_uses_settings_city(self, monkeypatch):
        get_settings.cache_clear()
        load_city_config.cache_clear()
        monkeypatch.setenv("CITY", "fort-worth")
        try:
            cfg = get_city_config()
            assert cfg.name == "Fort Worth"
        finally:
            get_settings.cache_clear()
            load_city_config.cache_clear()
