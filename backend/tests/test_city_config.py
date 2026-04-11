"""Tests for CityConfig schema and YAML loader."""

import pytest
import yaml

from pathlib import Path


CITIES_DIR = Path(__file__).resolve().parent.parent.parent / "cities"


class TestCityConfigModel:
    def test_valid_config(self):
        from app.cities.config import CityConfig

        cfg = CityConfig(
            name="Montgomery",
            state="AL",
            zip_ranges=["36101-36120"],
            job_adapters=["brightdata"],
            data_dir="data/montgomery",
        )
        assert cfg.name == "Montgomery"
        assert cfg.state == "AL"
        assert cfg.zip_ranges == ["36101-36120"]
        assert cfg.job_adapters == ["brightdata"]
        assert cfg.data_dir == "data/montgomery"

    def test_missing_name_raises(self):
        from app.cities.config import CityConfig

        with pytest.raises(Exception):
            CityConfig(
                state="AL",
                zip_ranges=["36101"],
                job_adapters=["brightdata"],
                data_dir="data/montgomery",
            )

    def test_missing_state_raises(self):
        from app.cities.config import CityConfig

        with pytest.raises(Exception):
            CityConfig(
                name="Montgomery",
                zip_ranges=["36101"],
                job_adapters=["brightdata"],
                data_dir="data/montgomery",
            )

    def test_missing_zip_ranges_raises(self):
        from app.cities.config import CityConfig

        with pytest.raises(Exception):
            CityConfig(
                name="Montgomery",
                state="AL",
                job_adapters=["brightdata"],
                data_dir="data/montgomery",
            )

    def test_missing_job_adapters_raises(self):
        from app.cities.config import CityConfig

        with pytest.raises(Exception):
            CityConfig(
                name="Montgomery",
                state="AL",
                zip_ranges=["36101"],
                data_dir="data/montgomery",
            )

    def test_missing_data_dir_raises(self):
        from app.cities.config import CityConfig

        with pytest.raises(Exception):
            CityConfig(
                name="Montgomery",
                state="AL",
                zip_ranges=["36101"],
                job_adapters=["brightdata"],
            )

    def test_zip_ranges_must_be_list(self):
        from app.cities.config import CityConfig

        with pytest.raises(Exception):
            CityConfig(
                name="Montgomery",
                state="AL",
                zip_ranges="36101",
                job_adapters=["brightdata"],
                data_dir="data/montgomery",
            )

    def test_job_adapters_must_be_list(self):
        from app.cities.config import CityConfig

        with pytest.raises(Exception):
            CityConfig(
                name="Montgomery",
                state="AL",
                zip_ranges=["36101"],
                job_adapters="brightdata",
                data_dir="data/montgomery",
            )


class TestLoadCityConfig:
    def test_load_montgomery(self):
        from app.cities.config import load_city_config

        cfg = load_city_config("montgomery")
        assert cfg.name == "Montgomery"
        assert cfg.state == "AL"
        assert len(cfg.zip_ranges) > 0
        assert len(cfg.job_adapters) > 0
        assert cfg.data_dir

    def test_load_fort_worth(self):
        from app.cities.config import load_city_config

        cfg = load_city_config("fort-worth")
        assert cfg.name == "Fort Worth"
        assert cfg.state == "TX"
        assert len(cfg.zip_ranges) > 0
        assert len(cfg.job_adapters) > 0

    def test_load_nonexistent_raises(self):
        from app.cities.config import CityConfigNotFoundError, load_city_config

        with pytest.raises(CityConfigNotFoundError, match="nonexistent"):
            load_city_config("nonexistent")

    def test_error_message_includes_city_name(self):
        from app.cities.config import CityConfigNotFoundError, load_city_config

        with pytest.raises(CityConfigNotFoundError) as exc_info:
            load_city_config("atlantis")
        assert "atlantis" in str(exc_info.value)

    def test_loaded_config_matches_yaml(self):
        from app.cities.config import load_city_config

        cfg = load_city_config("montgomery")
        yaml_path = CITIES_DIR / "montgomery.yaml"
        with open(yaml_path) as f:
            raw = yaml.safe_load(f)
        assert cfg.name == raw["name"]
        assert cfg.state == raw["state"]
        assert cfg.zip_ranges == raw["zip_ranges"]


class TestCitySettingInConfig:
    def test_default_city_is_montgomery(self):
        from app.core.config import Settings

        s = Settings(
            _env_file=None,
            anthropic_api_key="test",
        )
        assert s.city == "montgomery"

    def test_city_can_be_overridden(self):
        from app.core.config import Settings

        s = Settings(
            _env_file=None,
            city="fort-worth",
            anthropic_api_key="test",
        )
        assert s.city == "fort-worth"

    def test_existing_settings_unchanged(self):
        from app.core.config import Settings

        s = Settings(
            _env_file=None,
            anthropic_api_key="test",
        )
        assert s.app_name == "MontGoWork"
        assert s.environment == "development"


class TestMontgomeryYaml:
    def test_validates_against_schema(self):
        from app.cities.config import load_city_config

        cfg = load_city_config("montgomery")
        assert cfg.name == "Montgomery"
        assert cfg.state == "AL"

    def test_has_expected_adapters(self):
        from app.cities.config import load_city_config

        cfg = load_city_config("montgomery")
        assert cfg.job_adapters == ["brightdata", "honestjobs"]

    def test_has_zip_ranges(self):
        from app.cities.config import load_city_config

        cfg = load_city_config("montgomery")
        assert len(cfg.zip_ranges) >= 3
        assert any("36101" in z for z in cfg.zip_ranges)

    def test_data_dir_points_to_cities_subdir(self):
        from app.cities.config import load_city_config

        cfg = load_city_config("montgomery")
        assert cfg.data_dir == "data/cities/montgomery"


class TestFortWorthYaml:
    def test_validates_against_schema(self):
        from app.cities.config import load_city_config

        cfg = load_city_config("fort-worth")
        assert cfg.name == "Fort Worth"
        assert cfg.state == "TX"

    def test_has_expected_adapters(self):
        from app.cities.config import load_city_config

        cfg = load_city_config("fort-worth")
        assert cfg.job_adapters == ["twc", "usajobs"]

    def test_has_zip_ranges(self):
        from app.cities.config import load_city_config

        cfg = load_city_config("fort-worth")
        assert len(cfg.zip_ranges) >= 1
        assert any("76" in z for z in cfg.zip_ranges)

    def test_data_dir_points_to_cities_subdir(self):
        from app.cities.config import load_city_config

        cfg = load_city_config("fort-worth")
        assert cfg.data_dir == "data/cities/fort-worth"


class TestDataDirectories:
    def test_montgomery_data_dir_has_gitkeep(self):
        gitkeep = Path(__file__).resolve().parent.parent.parent / "data" / "cities" / "montgomery" / ".gitkeep"
        assert gitkeep.exists()

    def test_fort_worth_data_dir_has_gitkeep(self):
        gitkeep = Path(__file__).resolve().parent.parent.parent / "data" / "cities" / "fort-worth" / ".gitkeep"
        assert gitkeep.exists()


class TestGetCityConfig:
    def test_returns_config_for_default_city(self):
        from app.cities.config import get_city_config

        cfg = get_city_config()
        assert cfg.name == "Montgomery"

    def test_uses_settings_city(self, monkeypatch):
        from app.core.config import get_settings

        get_settings.cache_clear()
        monkeypatch.setenv("CITY", "fort-worth")
        try:
            from app.cities.config import get_city_config

            cfg = get_city_config()
            assert cfg.name == "Fort Worth"
        finally:
            get_settings.cache_clear()
