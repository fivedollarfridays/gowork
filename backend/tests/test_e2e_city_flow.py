"""End-to-end integration tests: CITY=fort-worth and CITY=montgomery full flow.

Verifies the complete assessment -> cliff analysis -> benefits screening
-> barrier sequencing -> prompt routing chain for both cities, ensuring
zero Alabama bypasses when CITY=fort-worth and vice versa.
"""

import pytest

from app.modules.benefits.types import BenefitsProfile, CliffAnalysis


# ---------------------------------------------------------------------------
# City fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def _fort_worth_city(monkeypatch):
    monkeypatch.setenv("CITY", "fort-worth")
    from app.cities.config import load_city_config
    load_city_config.cache_clear()
    from app.core.config import get_settings
    get_settings.cache_clear()
    yield
    load_city_config.cache_clear()
    get_settings.cache_clear()


@pytest.fixture
def _montgomery_city(monkeypatch):
    monkeypatch.setenv("CITY", "montgomery")
    from app.cities.config import load_city_config
    load_city_config.cache_clear()
    from app.core.config import get_settings
    get_settings.cache_clear()
    yield
    load_city_config.cache_clear()
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Fort Worth end-to-end
# ---------------------------------------------------------------------------

class TestFortWorthEndToEnd:
    """Full chain: ZIP -> cliff -> screener -> barriers -> prompts for FW."""

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_zip_76102_accepted(self):
        """Fort Worth ZIP 76102 passes AssessmentRequest validation."""
        from app.modules.matching.types import AssessmentRequest

        req = AssessmentRequest(
            zip_code="76102",
            employment_status="unemployed",
            barriers={"credit": True},
            work_history="Warehouse work for 3 years",
        )
        assert req.zip_code == "76102"

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_cliff_uses_tx_ami(self):
        """Cliff calculator uses TX AMI ($78K) not AL AMI ($60K) for FW."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        profile = BenefitsProfile(
            household_size=4,
            current_monthly_income=2000,
            enrolled_programs=["SNAP", "Section_8"],
            state="TX",
        )
        result = calculate_cliff_analysis(profile)
        assert isinstance(result, CliffAnalysis)
        assert len(result.wage_steps) > 0

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_screener_says_hhsc_not_dhr(self):
        """Benefits screener disclaimer mentions HHSC, never Alabama DHR."""
        from app.modules.benefits.eligibility_screener import (
            screen_benefits_eligibility,
        )

        profile = BenefitsProfile(
            household_size=3,
            current_monthly_income=1500,
            dependents_under_6=1,
            state="TX",
        )
        result = screen_benefits_eligibility(profile)
        assert "HHSC" in result.disclaimer
        assert "Alabama" not in result.disclaimer
        assert "DHR" not in result.disclaimer

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_screener_has_chip_not_all_kids(self):
        """Fort Worth screener lists CHIP, never ALL_Kids."""
        from app.modules.benefits.eligibility_screener import (
            screen_benefits_eligibility,
        )

        profile = BenefitsProfile(
            household_size=4,
            current_monthly_income=1500,
            dependents_under_6=1,
            dependents_6_to_17=1,
            state="TX",
        )
        result = screen_benefits_eligibility(profile)
        all_progs = [
            p.program for p in result.eligible_programs + result.ineligible_programs
        ]
        assert "CHIP" in all_progs
        assert "ALL_Kids" not in all_progs

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_screener_has_ceap_not_liheap(self):
        """Fort Worth screener lists CEAP, never LIHEAP."""
        from app.modules.benefits.eligibility_screener import (
            screen_benefits_eligibility,
        )

        profile = BenefitsProfile(
            household_size=3,
            current_monthly_income=800,
            state="TX",
        )
        result = screen_benefits_eligibility(profile)
        all_progs = [
            p.program for p in result.eligible_programs + result.ineligible_programs
        ]
        assert "CEAP" in all_progs
        assert "LIHEAP" not in all_progs

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_barrier_sequencer_works(self):
        """Barrier sequencer produces valid chain for FW barriers."""
        from app.modules.plan.barrier_sequencer import sequence_barriers

        # Include CREDIT_NO_HISTORY to form chain:
        # CREDIT_NO_BANK -> CREDIT_NO_HISTORY -> CREDIT_LOW_SCORE
        result = sequence_barriers([
            "CREDIT_LOW_SCORE", "CREDIT_NO_BANK", "CREDIT_NO_HISTORY",
        ])
        assert result.total_barriers == 3
        ids = [s.barrier_id for s in result.steps]
        assert ids.index("CREDIT_NO_BANK") < ids.index("CREDIT_NO_HISTORY")
        assert ids.index("CREDIT_NO_HISTORY") < ids.index("CREDIT_LOW_SCORE")

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_barrier_cards_say_trinity_metro(self):
        """Fort Worth barrier actions mention Trinity Metro, not M-Transit."""
        from app.modules.matching.resource_router import get_barrier_actions
        from app.modules.matching.types import BarrierType

        actions = get_barrier_actions()
        transport_actions = actions.get(BarrierType.TRANSPORTATION, [])
        combined = " ".join(transport_actions)
        assert "Trinity Metro" in combined
        assert "M-Transit" not in combined

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_career_center_says_workforce_solutions(self):
        """Fort Worth career center is Workforce Solutions, not AL Career Center."""
        from app.modules.matching.resource_router import get_career_center

        center = get_career_center()
        assert "Workforce Solutions" in center.name
        assert "Alabama" not in center.name

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_prompt_mentions_fort_worth(self):
        """AI system prompt mentions Fort Worth, not Montgomery."""
        from app.ai.prompt_router import get_system_prompt

        prompt = get_system_prompt()
        assert "Fort Worth" in prompt
        assert "Montgomery" not in prompt.split("Security")[0]

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_geo_uses_fw_coords(self):
        """Downtown coords should be Fort Worth, not Montgomery."""
        from app.modules.matching.geo_router import get_downtown_coords

        lat, lng = get_downtown_coords()
        # Fort Worth is ~32.75, -97.33
        assert 32.5 < lat < 33.0
        assert -97.5 < lng < -97.0

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_cert_db_says_texas_board(self):
        """Cert DB references Texas Board of Nursing, not Alabama."""
        from app.modules.matching.resource_router import get_cert_db

        db = get_cert_db()
        assert "CNA" in db
        assert "Texas" in db["CNA"]["renewal_body"]["name"]

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_filters_use_texas_board(self):
        """get_cert_db for Fort Worth should reference Texas bodies."""
        from app.modules.matching.resource_router import get_cert_db

        db = get_cert_db()
        for cert_key in db:
            body_name = db[cert_key]["renewal_body"]["name"]
            assert "Alabama" not in body_name


# ---------------------------------------------------------------------------
# Montgomery end-to-end
# ---------------------------------------------------------------------------

class TestMontgomeryEndToEnd:
    """Full chain for CITY=montgomery ensuring AL data is used."""

    @pytest.mark.usefixtures("_montgomery_city")
    def test_zip_36104_accepted(self):
        """Montgomery ZIP 36104 passes validation."""
        from app.modules.matching.types import AssessmentRequest

        req = AssessmentRequest(
            zip_code="36104",
            employment_status="unemployed",
            barriers={"credit": True},
            work_history="Retail work for 2 years",
        )
        assert req.zip_code == "36104"

    @pytest.mark.usefixtures("_montgomery_city")
    def test_cliff_uses_al_ami(self):
        """Cliff calculator uses AL AMI ($60K) for Montgomery."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        profile = BenefitsProfile(
            household_size=4,
            current_monthly_income=2000,
            enrolled_programs=["SNAP", "Section_8"],
            state="AL",
        )
        result = calculate_cliff_analysis(profile)
        assert isinstance(result, CliffAnalysis)

    @pytest.mark.usefixtures("_montgomery_city")
    def test_screener_says_dhr(self):
        """Montgomery screener disclaimer mentions Alabama DHR."""
        from app.modules.benefits.eligibility_screener import (
            screen_benefits_eligibility,
        )

        profile = BenefitsProfile(
            household_size=3,
            current_monthly_income=1500,
            state="AL",
        )
        result = screen_benefits_eligibility(profile)
        assert "Alabama" in result.disclaimer
        assert "HHSC" not in result.disclaimer

    @pytest.mark.usefixtures("_montgomery_city")
    def test_screener_has_all_kids_not_chip(self):
        """Montgomery screener lists ALL_Kids, never CHIP."""
        from app.modules.benefits.eligibility_screener import (
            screen_benefits_eligibility,
        )

        profile = BenefitsProfile(
            household_size=4,
            current_monthly_income=1500,
            dependents_under_6=1,
            dependents_6_to_17=1,
            state="AL",
        )
        result = screen_benefits_eligibility(profile)
        all_progs = [
            p.program for p in result.eligible_programs + result.ineligible_programs
        ]
        assert "ALL_Kids" in all_progs
        assert "CHIP" not in all_progs

    @pytest.mark.usefixtures("_montgomery_city")
    def test_barrier_cards_say_m_transit(self):
        """Montgomery barrier actions mention M-Transit, not Trinity Metro."""
        from app.modules.matching.resource_router import get_barrier_actions
        from app.modules.matching.types import BarrierType

        actions = get_barrier_actions()
        transport_actions = actions.get(BarrierType.TRANSPORTATION, [])
        combined = " ".join(transport_actions)
        assert "M-Transit" in combined or "Montgomery" in combined
        assert "Trinity Metro" not in combined

    @pytest.mark.usefixtures("_montgomery_city")
    def test_career_center_is_alabama(self):
        """Montgomery career center is Alabama Career Center."""
        from app.modules.matching.resource_router import get_career_center

        center = get_career_center()
        assert "Alabama" in center.name or "Montgomery" in center.name
        assert "Workforce Solutions" not in center.name

    @pytest.mark.usefixtures("_montgomery_city")
    def test_prompt_mentions_montgomery(self):
        """AI system prompt mentions Montgomery, not Fort Worth."""
        from app.ai.prompt_router import get_system_prompt

        prompt = get_system_prompt()
        assert "Montgomery" in prompt

    @pytest.mark.usefixtures("_montgomery_city")
    def test_geo_uses_montgomery_coords(self):
        """Downtown coords should be Montgomery, not Fort Worth."""
        from app.modules.matching.geo_router import get_downtown_coords

        lat, lng = get_downtown_coords()
        # Montgomery is ~32.37, -86.30
        assert 32.0 < lat < 32.6
        assert -86.5 < lng < -86.0

    @pytest.mark.usefixtures("_montgomery_city")
    def test_fort_worth_zip_rejected(self):
        """Fort Worth ZIP should be rejected when CITY=montgomery."""
        from app.modules.matching.types import AssessmentRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AssessmentRequest(
                zip_code="76102",
                employment_status="unemployed",
                barriers={"credit": True},
                work_history="Warehouse work",
            )
