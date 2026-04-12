"""Tests for criminal record clearing module routing."""

from unittest.mock import patch

from app.modules.criminal.record_profile import (
    ChargeCategory,
    RecordProfile,
    RecordType,
)


def _mock_city_config(state: str):
    from app.cities.config import CityConfig

    configs = {
        "AL": CityConfig(
            name="Montgomery", state="AL", location="Montgomery, AL",
            zip_ranges=["36101-36120"], job_adapters=["brightdata"],
            data_dir="data/cities/montgomery",
        ),
        "TX": CityConfig(
            name="Fort Worth", state="TX", location="Fort Worth, TX",
            zip_ranges=["76101-76199"], job_adapters=["twc"],
            data_dir="data/cities/fort-worth",
        ),
    }
    return configs[state]


class TestCriminalRouter:
    def test_alabama_uses_expungement(self):
        from app.modules.criminal.router import check_record_clearing

        profile = RecordProfile(
            record_types=[RecordType.ARREST_ONLY],
            charge_categories=[ChargeCategory.OTHER],
        )
        with patch("app.modules.criminal.router.get_city_config", return_value=_mock_city_config("AL")):
            result = check_record_clearing(profile)
            # Alabama returns ExpungementResult directly
            from app.modules.criminal.expungement import ExpungementResult
            assert isinstance(result, ExpungementResult)

    def test_texas_uses_record_clearing(self):
        from app.modules.criminal.router import check_record_clearing

        profile = RecordProfile(
            record_types=[RecordType.ARREST_ONLY],
            charge_categories=[ChargeCategory.OTHER],
        )
        with patch("app.modules.criminal.router.get_city_config", return_value=_mock_city_config("TX")):
            result = check_record_clearing(profile)
            from app.modules.criminal.texas_expunction import TexasRecordClearingResult
            assert isinstance(result, TexasRecordClearingResult)

    def test_texas_result_has_expunction_eligible(self):
        from app.modules.criminal.router import check_record_clearing

        profile = RecordProfile(
            record_types=[RecordType.ARREST_ONLY],
            charge_categories=[ChargeCategory.OTHER],
        )
        with patch("app.modules.criminal.router.get_city_config", return_value=_mock_city_config("TX")):
            result = check_record_clearing(profile)
            assert result.expunction_eligible

    def test_none_profile_handled(self):
        from app.modules.criminal.router import check_record_clearing

        with patch("app.modules.criminal.router.get_city_config", return_value=_mock_city_config("AL")):
            result = check_record_clearing(None)
            assert result is not None

        with patch("app.modules.criminal.router.get_city_config", return_value=_mock_city_config("TX")):
            result = check_record_clearing(None)
            assert result is not None
