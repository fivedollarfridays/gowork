"""Tests for Fort Worth resources, barrier cards, and career center."""

import pytest


class TestFortWorthCareerCenter:
    def test_career_center_info(self):
        from app.modules.matching.fort_worth_resources import CAREER_CENTER

        assert "Workforce Solutions" in CAREER_CENTER.name
        assert "Tarrant" in CAREER_CENTER.name
        assert "Fort Worth" in CAREER_CENTER.address
        assert CAREER_CENTER.phone

    def test_career_center_has_transit(self):
        from app.modules.matching.fort_worth_resources import CAREER_CENTER

        assert CAREER_CENTER.transit_route


class TestFortWorthBarrierActions:
    def test_all_barrier_types_have_actions(self):
        from app.modules.matching.fort_worth_resources import BARRIER_ACTIONS
        from app.modules.matching.types import BarrierType

        for bt in BarrierType:
            assert bt in BARRIER_ACTIONS, f"Missing actions for {bt}"
            assert len(BARRIER_ACTIONS[bt]) >= 2

    def test_transportation_mentions_trinity_metro(self):
        from app.modules.matching.fort_worth_resources import BARRIER_ACTIONS
        from app.modules.matching.types import BarrierType

        actions = BARRIER_ACTIONS[BarrierType.TRANSPORTATION]
        combined = " ".join(actions).lower()
        assert "trinity metro" in combined

    def test_childcare_mentions_twc(self):
        from app.modules.matching.fort_worth_resources import BARRIER_ACTIONS
        from app.modules.matching.types import BarrierType

        actions = BARRIER_ACTIONS[BarrierType.CHILDCARE]
        combined = " ".join(actions).lower()
        assert "twc" in combined or "workforce solutions" in combined or "texas" in combined


class TestFortWorthCertDB:
    def test_cert_db_has_cna_cdl_lpn(self):
        from app.modules.matching.fort_worth_resources import CERT_DB

        assert "CNA" in CERT_DB
        assert "CDL" in CERT_DB
        assert "LPN" in CERT_DB

    def test_cna_uses_texas_board(self):
        from app.modules.matching.fort_worth_resources import CERT_DB

        cna = CERT_DB["CNA"]
        assert "Texas" in cna["renewal_body"]["name"]


class TestFortWorthResourceAffinity:
    def test_affinity_has_trinity_metro(self):
        from app.modules.matching.fort_worth_resources import RESOURCE_AFFINITY
        from app.modules.matching.types import BarrierType

        # At least one keyword should map to TRANSPORTATION
        transport_keywords = [k for k, v in RESOURCE_AFFINITY.items() if v == BarrierType.TRANSPORTATION]
        combined = " ".join(transport_keywords)
        assert "trinity" in combined or "metro" in combined


class TestResourceRouter:
    def test_routes_to_montgomery_for_al(self):
        from unittest.mock import patch
        from app.modules.matching.resource_router import get_career_center
        from app.cities.config import CityConfig

        cfg = CityConfig(
            name="Montgomery", state="AL", location="Montgomery, AL",
            zip_ranges=["36101-36120"], job_adapters=["brightdata"],
            data_dir="data/cities/montgomery",
        )
        with patch("app.modules.matching.resource_router.get_city_config", return_value=cfg):
            cc = get_career_center()
            assert "Montgomery" in cc.name

    def test_routes_to_fort_worth_for_tx(self):
        from unittest.mock import patch
        from app.modules.matching.resource_router import get_career_center
        from app.cities.config import CityConfig

        cfg = CityConfig(
            name="Fort Worth", state="TX", location="Fort Worth, TX",
            zip_ranges=["76101-76199"], job_adapters=["twc"],
            data_dir="data/cities/fort-worth",
        )
        with patch("app.modules.matching.resource_router.get_city_config", return_value=cfg):
            cc = get_career_center()
            assert "Workforce Solutions" in cc.name or "Tarrant" in cc.name
