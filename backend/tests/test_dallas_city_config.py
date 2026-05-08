"""Tests for the Dallas (TX) city skeleton — Sprint 25 entry task.

Sprint 25 is *additive*: every consumer of ``get_city_config()`` already
dispatches via ``city.state == "TX"`` guards, so Dallas inherits all
TX state-level work for free.  These tests pin the schema parity that
makes that inheritance safe.

Mirrors the pattern from ``test_city_config.py::TestFortWorthYaml`` and
``app/cities/fort_worth/`` so the two TX cities stay in lockstep.
"""

from pathlib import Path

import yaml

from app.cities.config import CityConfig, load_city_config


CITIES_DIR = Path(__file__).resolve().parent.parent.parent / "cities"
FW_YAML = CITIES_DIR / "fort-worth.yaml"
DALLAS_YAML = CITIES_DIR / "dallas.yaml"


def _load_raw(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestDallasCityConfigLoads:
    def test_load_returns_city_config(self):
        cfg = load_city_config("dallas")
        assert isinstance(cfg, CityConfig)

    def test_name_is_dallas(self):
        cfg = load_city_config("dallas")
        assert cfg.name == "Dallas"

    def test_state_is_tx(self):
        cfg = load_city_config("dallas")
        assert cfg.state == "TX"

    def test_location_is_dallas_tx(self):
        cfg = load_city_config("dallas")
        assert cfg.location == "Dallas, TX"

    def test_zip_ranges_cover_75201_75398(self):
        cfg = load_city_config("dallas")
        assert cfg.zip_ranges == ["75201-75398"]

    def test_job_adapters_includes_honestjobs(self):
        # T25.3 wired honestjobs once
        # backend/data/cities/dallas/honestjobs_listings.json landed.
        # The full Dallas adapter set now mirrors Fort Worth's.
        cfg = load_city_config("dallas")
        assert cfg.job_adapters == ["twc", "usajobs", "honestjobs"]
        assert "honestjobs" in cfg.job_adapters

    def test_data_dir_points_to_cities_subdir(self):
        cfg = load_city_config("dallas")
        assert cfg.data_dir == "data/cities/dallas"


class TestDallasAppointmentServicesParity:
    """Dallas must mirror Fort Worth's appointment_services schema exactly.

    Both cities are America/Chicago; sharing the schema lets
    ``app/modules/appointments/availability.py`` work for either city
    without per-city branching.
    """

    def test_yaml_has_appointment_services_block(self):
        raw = _load_raw(DALLAS_YAML)
        assert "appointment_services" in raw

    def test_appointment_service_keys_match_fw(self):
        dallas_raw = _load_raw(DALLAS_YAML)
        fw_raw = _load_raw(FW_YAML)
        assert set(dallas_raw["appointment_services"].keys()) == set(
            fw_raw["appointment_services"].keys()
        )

    def test_each_service_has_hours_and_closed_days(self):
        dallas_raw = _load_raw(DALLAS_YAML)
        fw_raw = _load_raw(FW_YAML)
        for svc, fw_spec in fw_raw["appointment_services"].items():
            d_spec = dallas_raw["appointment_services"][svc]
            # same keys present in each per-service block
            assert set(d_spec.keys()) == set(fw_spec.keys())
            # hours_local shape: list[list[str]] (e.g. [["09:00","12:00"], ...])
            assert isinstance(d_spec["hours_local"], list)
            for window in d_spec["hours_local"]:
                assert isinstance(window, list)
                assert len(window) == 2
                assert all(isinstance(t, str) for t in window)
            # closed_days_of_week is a list of ints (0=Mon..6=Sun)
            assert isinstance(d_spec["closed_days_of_week"], list)
            assert all(isinstance(d, int) for d in d_spec["closed_days_of_week"])

    def test_appointment_service_values_match_fw(self):
        # Sister-city parity: same hours, same closed days, same durations.
        dallas_raw = _load_raw(DALLAS_YAML)
        fw_raw = _load_raw(FW_YAML)
        assert dallas_raw["appointment_services"] == fw_raw["appointment_services"]


class TestDallasModuleSkeleton:
    def test_dallas_module_imports(self):
        import app.cities.dallas as dallas_mod

        assert dallas_mod is not None

    def test_dallas_module_has_state_gating_warning(self):
        import app.cities.dallas as dallas_mod

        # The package docstring must warn importers to gate on state=="TX",
        # mirroring fort_worth/__init__.py exactly.
        doc = dallas_mod.__doc__ or ""
        assert 'city.state == "TX"' in doc

    def test_eligibility_rules_dict_exists(self):
        from app.cities.dallas.eligibility import DALLAS_ELIGIBILITY_RULES

        assert isinstance(DALLAS_ELIGIBILITY_RULES, dict)
        assert len(DALLAS_ELIGIBILITY_RULES) > 0

    def test_required_open_resources_present(self):
        from app.cities.dallas.eligibility import DALLAS_ELIGIBILITY_RULES

        required_open = [
            "Workforce Solutions Greater Dallas",
            "Dallas College",
            "DART",
            "Parkland Health",
            "Legal Aid of NorthWest Texas — Dallas",
            "Dallas Housing Authority",
            "Texas Rising Star",
            "North Texas 211",
        ]
        for resource in required_open:
            assert resource in DALLAS_ELIGIBILITY_RULES, (
                f"missing {resource!r} from DALLAS_ELIGIBILITY_RULES"
            )
            assert DALLAS_ELIGIBILITY_RULES[resource]["type"] == "open"

    def test_twc_childcare_uses_smi_threshold(self):
        from app.cities.dallas.eligibility import DALLAS_ELIGIBILITY_RULES
        from app.modules.benefits.thresholds import CHILDCARE_SMI_LIMIT_PCT

        rule = DALLAS_ELIGIBILITY_RULES["TWC Child Care Services"]
        assert rule["type"] == "compound"
        assert rule["income_check"] == "smi"
        assert rule["max_income_pct_smi"] == CHILDCARE_SMI_LIMIT_PCT
        assert rule["requires_any_children"] is True
