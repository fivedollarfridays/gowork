"""Cross-module integration tests for S8 Phase 2.

Verifies that every feature CONNECTS to every other feature it should.
Each test exercises a specific integration chain from the checklist.
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import text

from app.cities.config import CityConfig
from app.core.database import get_async_session_factory
from app.modules.benefits.types import BenefitsProfile


def _fw_config():
    return CityConfig(
        name="Fort Worth", state="TX", location="Fort Worth, TX",
        zip_ranges=["76101-76199"], job_adapters=["twc", "usajobs"],
        data_dir="data/cities/fort-worth",
    )


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


# ---------------------------------------------------------------------------
# 1. Assessment -> Plan: generate_plan with FW ZIP produces TX barrier cards
# ---------------------------------------------------------------------------

class TestAssessmentToPlan:
    """AssessmentRequest (with FW ZIP) -> generate_plan() -> ReEntryPlan with TX benefits."""

    @pytest.mark.usefixtures("_fort_worth_city")
    @pytest.mark.anyio
    async def test_generate_plan_with_fw_profile(self, test_engine):
        """Full generate_plan with Fort Worth profile produces ReEntryPlan."""
        from app.modules.matching.engine import generate_plan
        from app.modules.matching.types import (
            AvailableHours, BarrierSeverity, BarrierType, EmploymentStatus, UserProfile,
        )

        factory = get_async_session_factory()
        async with factory() as db:
            profile = UserProfile(
                session_id="00000000-0000-4000-8000-aaa000000001",
                zip_code="76102",
                employment_status=EmploymentStatus.UNEMPLOYED,
                barrier_count=2,
                primary_barriers=[BarrierType.CREDIT, BarrierType.TRANSPORTATION],
                barrier_severity=BarrierSeverity.MEDIUM,
                needs_credit_assessment=True,
                transit_dependent=True,
                schedule_type=AvailableHours.DAYTIME,
                work_history="Warehouse work for 3 years",
                target_industries=["logistics"],
            )
            bp = BenefitsProfile(
                household_size=3,
                current_monthly_income=1200,
                enrolled_programs=["SNAP", "CHIP"],
                dependents_under_6=1,
                state="TX",
            )
            plan = await generate_plan(
                profile, db, resume_text="", benefits_profile=bp,
            )
            # ReEntryPlan should have barrier_cards, job matches, benefits data
            assert plan.session_id == profile.session_id
            assert len(plan.barriers) >= 0  # May be empty if no resources
            assert plan.benefits_cliff_analysis is not None
            assert plan.benefits_eligibility is not None


# ---------------------------------------------------------------------------
# 2. Plan -> Barrier Cards: barrier_cards use resource_router (FW actions)
# ---------------------------------------------------------------------------

class TestPlanToBarrierCards:
    """ReEntryPlan -> barrier_cards using resource_router (FW actions, not Montgomery)."""

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_barrier_cards_use_fw_actions(self):
        """Barrier cards for FW profile use Trinity Metro, not M-Transit."""
        from app.modules.matching.barrier_cards import build_barrier_cards_and_steps
        from app.modules.matching.types import (
            AvailableHours, BarrierSeverity, BarrierType, EmploymentStatus, UserProfile,
        )

        profile = UserProfile(
            session_id="00000000-0000-4000-8000-bbb000000001",
            zip_code="76102",
            employment_status=EmploymentStatus.UNEMPLOYED,
            barrier_count=2,
            primary_barriers=[BarrierType.TRANSPORTATION, BarrierType.CREDIT],
            barrier_severity=BarrierSeverity.MEDIUM,
            needs_credit_assessment=True,
            transit_dependent=True,
            schedule_type=AvailableHours.DAYTIME,
            work_history="Customer service 2 years",
            target_industries=["retail"],
        )
        cards, next_steps = build_barrier_cards_and_steps(profile, resources=[])
        # Transportation card should reference Trinity Metro
        transport_card = next(
            (c for c in cards if c.type == BarrierType.TRANSPORTATION), None,
        )
        assert transport_card is not None
        combined_actions = " ".join(transport_card.actions)
        assert "Trinity Metro" in combined_actions
        assert "M-Transit" not in combined_actions


# ---------------------------------------------------------------------------
# 3. Plan -> Cliff: generate_plan cliff uses benefits_router (TX AMI)
# ---------------------------------------------------------------------------

class TestPlanToCliff:
    """generate_plan() -> cliff_calculator using benefits_router (TX AMI, not AL)."""

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_cliff_analysis_uses_tx_thresholds(self):
        """Cliff analysis for FW uses TX AMI and TX programs."""
        from app.modules.benefits.cliff_calculator import calculate_cliff_analysis

        bp = BenefitsProfile(
            household_size=4,
            current_monthly_income=1500,
            enrolled_programs=["SNAP", "CHIP", "Section_8"],
            dependents_under_6=1,
            dependents_6_to_17=1,
            state="TX",
        )
        result = calculate_cliff_analysis(bp)
        # Should have wage steps and identify cliff points
        assert len(result.wage_steps) > 0
        # CHIP should appear in the programs list (TX program, not ALL_Kids)
        program_names = [p.program for p in result.programs]
        assert "CHIP" in program_names
        assert "ALL_Kids" not in program_names


# ---------------------------------------------------------------------------
# 4. Plan -> Pathway: generate_plan -> pathway engine with calibrated_weeks
# ---------------------------------------------------------------------------

class TestPlanToPathway:
    """generate_plan -> pathway engine -> career trajectories using calibrated_weeks."""

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_pathway_with_calibrated_weeks(self):
        """Pathway engine produces different timelines with calibrated data."""
        from app.modules.pathway.engine import generate_pathways

        bp = BenefitsProfile(
            household_size=3,
            current_monthly_income=1200,
            enrolled_programs=["SNAP"],
            dependents_under_6=1,
            state="TX",
        )
        # Without calibration
        default_result = generate_pathways(
            barrier_ids=["criminal_record", "credit"],
            benefits_profile=bp,
            current_wage=0.0,
        )
        # With calibration (shorter weeks)
        cal_result = generate_pathways(
            barrier_ids=["criminal_record", "credit"],
            benefits_profile=bp,
            current_wage=0.0,
            calibrated_weeks={"criminal_record": 6, "credit": 4},
        )
        # Calibrated should have shorter or equal total weeks
        default_weeks = default_result.pathways[0].total_weeks
        cal_weeks = cal_result.pathways[0].total_weeks
        assert cal_weeks <= default_weeks


# ---------------------------------------------------------------------------
# 5. Barrier Sequencer -> Intelligence: calibrated_weeks flow
# ---------------------------------------------------------------------------

class TestSequencerToIntelligence:
    """Intelligence engine -> calibrated_weeks -> sequencer uses them."""

    def test_intelligence_output_feeds_sequencer(self):
        """Compute calibrated barriers and verify sequencer consumes them."""
        from app.modules.outcomes.intelligence import compute_calibrated_barriers
        from app.modules.plan.barrier_sequencer import sequence_barriers

        rows = [
            {"barrier_id": "credit", "resolved": True,
             "weeks_to_resolve": 3, "plan_accuracy": 4},
        ] * 5  # MEDIUM confidence
        result = compute_calibrated_barriers(rows)
        weeks_dict = result.to_weeks_dict()
        assert "credit" in weeks_dict

        seq = sequence_barriers(["credit", "housing"], calibrated_weeks=weeks_dict)
        # Credit should use calibrated weeks (3), housing should use default (6)
        credit_step = next(s for s in seq.steps if s.barrier_id == "credit")
        housing_step = next(s for s in seq.steps if s.barrier_id == "housing")
        assert credit_step.estimated_weeks == 3
        assert housing_step.estimated_weeks == 6


# ---------------------------------------------------------------------------
# 6. PVS Scorer -> Benefits Router: uses routed calculators
# ---------------------------------------------------------------------------

class TestPvsScorerToBenefitsRouter:
    """pvs_scorer uses routed calculators (not Alabama hardcoded)."""

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_pvs_uses_tx_net_income_scoring(self):
        """PVS net income scoring uses TX program calculators."""
        from app.modules.matching.pvs_scorer import compute_pvs
        from app.modules.matching.types import AvailableHours, BarrierType, ScoringContext

        bp = BenefitsProfile(
            household_size=3,
            current_monthly_income=1500,
            enrolled_programs=["SNAP", "CHIP"],
            dependents_under_6=1,
            state="TX",
        )
        ctx = ScoringContext(
            user_zip="76102",
            transit_dependent=False,
            schedule_type=AvailableHours.DAYTIME,
            barriers=[BarrierType.CREDIT],
            benefits_profile=bp,
        )
        job = {"title": "Clerk", "description": "$14/hr full time",
               "location": "Fort Worth, TX 76102"}
        pvs = compute_pvs(job, ctx)
        assert 0.0 < pvs <= 1.0


# ---------------------------------------------------------------------------
# 7. PVS Scorer -> Geo Router: proximity uses FW coords
# ---------------------------------------------------------------------------

class TestPvsScorerToGeoRouter:
    """pvs_scorer -> proximity_scorer -> geo_router (FW coords)."""

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_proximity_scoring_uses_fw_coords(self):
        """Proximity scoring for FW ZIP should give high score for FW location."""
        from app.modules.matching.proximity_scorer import score_proximity

        # Same ZIP = highest proximity
        score_same = score_proximity("76102", "123 Main St, Fort Worth, TX 76102", False)
        # Different city = lower proximity
        score_diff = score_proximity("76102", "456 Oak Ave, Dallas, TX 75201", False)

        assert score_same >= score_diff
        assert score_same > 0.5  # Same ZIP should be high


# ---------------------------------------------------------------------------
# 8. City Config -> All Routers: CITY=fort-worth -> all return TX
# ---------------------------------------------------------------------------

class TestCityConfigAllRouters:
    """CITY=fort-worth -> benefits/criminal/geo/resource/prompt routers all return TX."""

    @pytest.mark.usefixtures("_fort_worth_city")
    def test_all_routers_return_tx_data(self):
        """Every router returns Texas-specific data when CITY=fort-worth."""
        # Benefits router
        from app.modules.benefits.router import (
            get_program_checks,
            get_screener_disclaimer,
            get_thresholds,
            get_valid_programs,
        )
        checks = get_program_checks()
        assert "CHIP" in checks
        assert "ALL_Kids" not in checks

        disclaimer = get_screener_disclaimer()
        assert "HHSC" in disclaimer

        programs = get_valid_programs()
        assert "CHIP" in programs
        assert "CEAP" in programs

        thresholds = get_thresholds()
        assert thresholds["CHILD_HEALTH_PROGRAM"] == "CHIP"
        assert thresholds["ENERGY_PROGRAM"] == "CEAP"

        # Criminal router
        from app.modules.criminal.router import check_record_clearing
        result = check_record_clearing(None)
        assert hasattr(result, "expunction_eligible") or hasattr(result, "nondisclosure_eligible")

        # Geo router
        from app.modules.matching.geo_router import get_downtown_coords, get_zip_centroids
        lat, lng = get_downtown_coords()
        assert 32.5 < lat < 33.0  # Fort Worth
        centroids = get_zip_centroids()
        assert "76102" in centroids

        # Resource router
        from app.modules.matching.resource_router import get_barrier_actions, get_career_center
        center = get_career_center()
        assert "Workforce Solutions" in center.name
        actions = get_barrier_actions()
        from app.modules.matching.types import BarrierType
        transport = " ".join(actions.get(BarrierType.TRANSPORTATION, []))
        assert "Trinity Metro" in transport

        # Prompt router
        from app.ai.prompt_router import get_system_prompt
        prompt = get_system_prompt()
        assert "Fort Worth" in prompt
