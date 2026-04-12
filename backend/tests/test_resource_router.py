"""Tests for resource routing by city config."""

from unittest.mock import patch

from app.cities.config import CityConfig


def _mock_city_config(state: str) -> CityConfig:
    city_map = {
        "AL": CityConfig(
            name="Montgomery", state="AL", location="Montgomery, AL",
            zip_ranges=["36101-36120"], job_adapters=["brightdata"],
            data_dir="data/cities/montgomery",
        ),
        "TX": CityConfig(
            name="Fort Worth", state="TX", location="Fort Worth, TX",
            zip_ranges=["76101-76199"], job_adapters=["twc", "usajobs"],
            data_dir="data/cities/fort-worth",
        ),
    }
    return city_map[state]


_PATCH_TARGET = "app.modules.matching.resource_router.get_city_config"


class TestGetCareerCenter:
    def test_returns_montgomery_for_al(self):
        from app.modules.matching.resource_router import get_career_center

        with patch(_PATCH_TARGET, return_value=_mock_city_config("AL")):
            cc = get_career_center()
            assert "Montgomery" in cc.name

    def test_returns_fort_worth_for_tx(self):
        from app.modules.matching.resource_router import get_career_center

        with patch(_PATCH_TARGET, return_value=_mock_city_config("TX")):
            cc = get_career_center()
            assert "Tarrant" in cc.name or "Fort Worth" in cc.name


class TestGetBarrierActions:
    def test_returns_dict_for_al(self):
        from app.modules.matching.resource_router import get_barrier_actions

        with patch(_PATCH_TARGET, return_value=_mock_city_config("AL")):
            actions = get_barrier_actions()
            assert isinstance(actions, dict)
            assert len(actions) > 0

    def test_returns_dict_for_tx(self):
        from app.modules.matching.resource_router import get_barrier_actions

        with patch(_PATCH_TARGET, return_value=_mock_city_config("TX")):
            actions = get_barrier_actions()
            assert isinstance(actions, dict)
            assert len(actions) > 0


class TestGetCareerCenterStep:
    def test_returns_string_for_al(self):
        from app.modules.matching.resource_router import get_career_center_step

        with patch(_PATCH_TARGET, return_value=_mock_city_config("AL")):
            step = get_career_center_step()
            assert isinstance(step, str)
            assert len(step) > 0

    def test_returns_string_for_tx(self):
        from app.modules.matching.resource_router import get_career_center_step

        with patch(_PATCH_TARGET, return_value=_mock_city_config("TX")):
            step = get_career_center_step()
            assert isinstance(step, str)
            assert len(step) > 0


class TestGetResourceAffinity:
    def test_returns_dict_for_al(self):
        from app.modules.matching.resource_router import get_resource_affinity

        with patch(_PATCH_TARGET, return_value=_mock_city_config("AL")):
            aff = get_resource_affinity()
            assert isinstance(aff, dict)

    def test_returns_dict_for_tx(self):
        from app.modules.matching.resource_router import get_resource_affinity

        with patch(_PATCH_TARGET, return_value=_mock_city_config("TX")):
            aff = get_resource_affinity()
            assert isinstance(aff, dict)


class TestGetCertDb:
    def test_returns_dict_for_al(self):
        from app.modules.matching.resource_router import get_cert_db

        with patch(_PATCH_TARGET, return_value=_mock_city_config("AL")):
            db = get_cert_db()
            assert isinstance(db, dict)

    def test_returns_dict_for_tx(self):
        from app.modules.matching.resource_router import get_cert_db

        with patch(_PATCH_TARGET, return_value=_mock_city_config("TX")):
            db = get_cert_db()
            assert isinstance(db, dict)
