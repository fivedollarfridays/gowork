"""Tests for the city/state filter in the job matcher.

Layer 2 of the city-aware jobs pipeline (defense-in-depth). Even when the
seed file is wrong, the matcher must drop listings whose location does
not end in the active city's state suffix (e.g. ``, TX`` for Fort Worth).
"""

from unittest.mock import patch

import pytest

from app.cities.config import CityConfig
from app.modules.matching.job_matcher import _filter_by_state


def _fw_config() -> CityConfig:
    return CityConfig(
        name="Fort Worth", state="TX", location="Fort Worth, TX",
        zip_ranges=["76101-76199"], job_adapters=["honestjobs"],
        data_dir="data/cities/fort-worth",
    )


def _mont_config() -> CityConfig:
    return CityConfig(
        name="Montgomery", state="AL", location="Montgomery, AL",
        zip_ranges=["36101-36120"], job_adapters=["honestjobs"],
        data_dir="data/cities/montgomery",
    )


class TestFilterByState:
    def test_keeps_active_state_only(self):
        """Mixed jobs → only active-state ones survive."""
        jobs = [
            {"title": "FW Job", "location": "Fort Worth, TX"},
            {"title": "AL Job", "location": "Montgomery, AL"},
        ]
        with patch(
            "app.modules.matching.job_matcher.get_city_config",
            return_value=_fw_config(),
        ):
            result = _filter_by_state(jobs)
        assert len(result) == 1
        assert result[0]["title"] == "FW Job"

    def test_keeps_metro_area_in_same_state(self):
        """Arlington TX, Hurst TX should pass the FW state filter."""
        jobs = [
            {"title": "Arlington", "location": "Arlington, TX"},
            {"title": "Hurst", "location": "Hurst, TX"},
            {"title": "Fort Worth", "location": "Fort Worth, TX"},
            {"title": "Out of State", "location": "Tulsa, OK"},
        ]
        with patch(
            "app.modules.matching.job_matcher.get_city_config",
            return_value=_fw_config(),
        ):
            result = _filter_by_state(jobs)
        titles = {j["title"] for j in result}
        assert titles == {"Arlington", "Hurst", "Fort Worth"}

    def test_montgomery_keeps_alabama_jobs_only(self):
        """CITY=montgomery filters to , AL listings."""
        jobs = [
            {"title": "AL", "location": "Montgomery, AL"},
            {"title": "TX", "location": "Fort Worth, TX"},
        ]
        with patch(
            "app.modules.matching.job_matcher.get_city_config",
            return_value=_mont_config(),
        ):
            result = _filter_by_state(jobs)
        assert len(result) == 1
        assert result[0]["title"] == "AL"

    def test_drops_listings_with_no_location(self):
        """Listings with empty/null location are dropped (cannot verify state)."""
        jobs = [
            {"title": "No location", "location": None},
            {"title": "Empty", "location": ""},
            {"title": "Good", "location": "Fort Worth, TX"},
        ]
        with patch(
            "app.modules.matching.job_matcher.get_city_config",
            return_value=_fw_config(),
        ):
            result = _filter_by_state(jobs)
        assert len(result) == 1
        assert result[0]["title"] == "Good"

    def test_case_insensitive_state_match(self):
        """', tx' or ', Tx' should still match TX state filter."""
        jobs = [
            {"title": "Lower", "location": "Fort Worth, tx"},
            {"title": "Mixed", "location": "Fort Worth, Tx"},
            {"title": "Upper", "location": "Fort Worth, TX"},
        ]
        with patch(
            "app.modules.matching.job_matcher.get_city_config",
            return_value=_fw_config(),
        ):
            result = _filter_by_state(jobs)
        assert len(result) == 3


class TestMatchJobsAppliesStateFilter:
    """Integration: match_jobs() drops out-of-state listings even when seeded."""

    @pytest.mark.anyio
    async def test_match_jobs_drops_wrong_state(self, test_engine, monkeypatch):
        """Mixed-state listings → only active-state pass through match_jobs."""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from app.cities.config import load_city_config
        from app.core.config import get_settings
        from app.modules.matching.job_matcher import match_jobs
        from app.modules.matching.types import (
            BarrierSeverity,
            BarrierType,
            EmploymentStatus,
            UserProfile,
        )

        monkeypatch.setenv("CITY", "fort-worth")
        get_settings.cache_clear()
        load_city_config.cache_clear()

        factory = async_sessionmaker(test_engine, class_=AsyncSession)
        async with factory() as session:
            # Seed two listings — one TX, one AL
            await session.execute(text(
                "INSERT INTO job_listings "
                "(title, company, location, description, url, source, "
                "scraped_at, credit_check) "
                "VALUES ('FW Cook', 'Compass', 'Fort Worth, TX', "
                "'Kitchen role', 'http://x', 'test', '2026-04-30', 'unknown')"
            ))
            await session.execute(text(
                "INSERT INTO job_listings "
                "(title, company, location, description, url, source, "
                "scraped_at, credit_check) "
                "VALUES ('AL Cook', 'Aramark', 'Montgomery, AL', "
                "'Kitchen role', 'http://y', 'test', '2026-04-30', 'unknown')"
            ))
            await session.commit()

            profile = UserProfile(
                session_id="test-fw",
                zip_code="76101",
                employment_status=EmploymentStatus.UNEMPLOYED,
                barrier_count=0,
                primary_barriers=[BarrierType.CREDIT],
                barrier_severity=BarrierSeverity.LOW,
                needs_credit_assessment=False,
                transit_dependent=False,
                schedule_type="daytime",
                work_history="Kitchen helper",
                target_industries=["food_service"],
            )
            ranked = await match_jobs(profile, session)

        titles = [r.title for r in ranked]
        assert "FW Cook" in titles
        assert "AL Cook" not in titles
