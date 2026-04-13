"""End-to-end integration tests for the N+1 intelligence pipeline.

Donatello Module 4: Proves calibrated_weeks flows from intelligence
computation through barrier_sequencer into the pathway engine.

Also tests:
- _safe_parse_list non-list JSON branch (coverage gap)
- PII non-exposure on intelligence endpoint (Donatello Module 6)
- Cold start behavior documentation
"""

import json

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session_factory
from app.modules.outcomes.intelligence import (
    CalibratedWeeks,
    ConfidenceLevel,
    compute_calibrated_barriers,
)
from app.modules.outcomes.intelligence_queries import (
    _safe_parse_list,
    get_barrier_feedback_rows,
)
from app.modules.plan.barrier_sequencer import (
    _WEEKS_PER_BARRIER,
    sequence_barriers,
)
from app.modules.benefits.types import BenefitsProfile
from app.modules.pathway.engine import generate_pathways


@pytest.fixture
async def db(test_engine):
    factory = get_async_session_factory()
    async with factory() as session:
        yield session


# -- _safe_parse_list coverage gap tests --


class TestSafeParseListBranches:
    """Cover the non-list JSON branch at intelligence_queries.py line 73."""

    def test_dict_json_returns_empty_list(self):
        result = _safe_parse_list('{"a": 1}')
        assert result == []

    def test_string_json_returns_empty_list(self):
        result = _safe_parse_list('"just a string"')
        assert result == []

    def test_int_json_returns_empty_list(self):
        result = _safe_parse_list("42")
        assert result == []

    def test_null_json_returns_empty_list(self):
        result = _safe_parse_list("null")
        assert result == []

    def test_bool_json_returns_empty_list(self):
        result = _safe_parse_list("true")
        assert result == []

    def test_valid_list_returns_list(self):
        result = _safe_parse_list('["a", "b"]')
        assert result == ["a", "b"]

    def test_empty_string_returns_empty_list(self):
        result = _safe_parse_list("")
        assert result == []

    def test_none_returns_empty_list(self):
        result = _safe_parse_list(None)
        assert result == []


# -- End-to-end pipeline tests --


class TestEndToEndPipeline:
    """Proves data flows: compute -> to_weeks_dict -> sequencer -> pathway."""

    def test_calibrated_weeks_flow_to_sequencer(self):
        """Intelligence output directly feeds barrier sequencer."""
        rows = [
            {"barrier_id": "criminal_record", "resolved": True,
             "weeks_to_resolve": 6, "plan_accuracy": 4},
        ] * 5  # 5 samples -> MEDIUM confidence
        result = compute_calibrated_barriers(rows)
        weeks_dict = result.to_weeks_dict()

        # Weeks dict should have criminal_record = 6
        assert weeks_dict == {"criminal_record": 6}

        # Feed into sequencer
        seq = sequence_barriers(
            ["criminal_record"], calibrated_weeks=weeks_dict,
        )
        step = seq.steps[0]
        assert step.estimated_weeks == 6  # calibrated, not default 12

    def test_calibrated_weeks_flow_to_pathway(self):
        """Intelligence output flows through to pathway engine."""
        rows = [
            {"barrier_id": "criminal_record", "resolved": True,
             "weeks_to_resolve": 6, "plan_accuracy": 4},
        ] * 5
        result = compute_calibrated_barriers(rows)
        weeks_dict = result.to_weeks_dict()

        profile = BenefitsProfile(
            household_size=3,
            current_monthly_income=1200.0,
            enrolled_programs=["SNAP"],
            dependents_under_6=1,
            dependents_6_to_17=0,
        )

        # With calibration
        cal_result = generate_pathways(
            barrier_ids=["criminal_record"],
            benefits_profile=profile,
            current_wage=0.0,
            calibrated_weeks=weeks_dict,
        )
        # Without calibration
        default_result = generate_pathways(
            barrier_ids=["criminal_record"],
            benefits_profile=profile,
            current_wage=0.0,
        )

        # Calibrated timeline should be shorter or equal
        cal_weeks = cal_result.pathways[0].total_weeks
        default_weeks = default_result.pathways[0].total_weeks
        assert cal_weeks <= default_weeks

    def test_empty_intelligence_gives_default_sequencer(self):
        """Cold start: empty intelligence -> empty weeks dict -> default sequencer."""
        result = compute_calibrated_barriers([])
        weeks_dict = result.to_weeks_dict()
        assert weeks_dict == {}

        seq = sequence_barriers(
            ["criminal_record"], calibrated_weeks=weeks_dict,
        )
        step = seq.steps[0]
        assert step.estimated_weeks == _WEEKS_PER_BARRIER["criminal_record"]

    def test_low_confidence_excluded_from_pipeline(self):
        """LOW confidence barriers are NOT passed to sequencer."""
        rows = [
            {"barrier_id": "criminal_record", "resolved": True,
             "weeks_to_resolve": 6, "plan_accuracy": 3},
        ]  # 1 sample -> LOW confidence
        result = compute_calibrated_barriers(rows)
        weeks_dict = result.to_weeks_dict()

        # Should be excluded
        assert "criminal_record" not in weeks_dict

        # Sequencer uses default
        seq = sequence_barriers(
            ["criminal_record"], calibrated_weeks=weeks_dict,
        )
        step = seq.steps[0]
        assert step.estimated_weeks == _WEEKS_PER_BARRIER["criminal_record"]


# -- DB query with non-list JSON (coverage for line 73) --


class TestDBQueryNonListJSON:
    """DB query edge cases for non-list JSON in barriers/outcomes columns."""

    @pytest.mark.anyio
    async def test_dict_barriers_json_produces_empty(self, db):
        """Barriers column is valid JSON dict -> no observations."""
        sid = "aaaaaaaa-bbbb-cccc-dddd-000000000001"
        await db.execute(
            text(
                "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                "VALUES (:id, '2026-01-01', :barriers, '2027-01-01')"
            ),
            {"id": sid, "barriers": '{"not": "a list"}'},
        )
        await db.commit()
        await db.execute(
            text(
                "INSERT INTO visit_feedback "
                "(session_id, submitted_at, made_it_to_center, outcomes, plan_accuracy) "
                "VALUES (:sid, '2026-03-01', 1, '[]', 3)"
            ),
            {"sid": sid},
        )
        await db.commit()
        rows = await get_barrier_feedback_rows(db)
        assert rows == []

    @pytest.mark.anyio
    async def test_dict_outcomes_json_no_resolves(self, db):
        """Outcomes column is valid JSON dict -> no barriers marked resolved."""
        sid = "aaaaaaaa-bbbb-cccc-dddd-000000000001"
        await db.execute(
            text(
                "INSERT INTO sessions (id, created_at, barriers, expires_at) "
                "VALUES (:id, '2026-01-01', :barriers, '2027-01-01')"
            ),
            {"id": sid, "barriers": json.dumps(["credit"])},
        )
        await db.commit()
        await db.execute(
            text(
                "INSERT INTO visit_feedback "
                "(session_id, submitted_at, made_it_to_center, outcomes, plan_accuracy) "
                "VALUES (:sid, '2026-03-01', 1, :outcomes, 3)"
            ),
            {"sid": sid, "outcomes": '{"not": "a list"}'},
        )
        await db.commit()
        rows = await get_barrier_feedback_rows(db)
        assert len(rows) == 1
        assert rows[0]["resolved"] is False


# -- PII non-exposure test (Donatello Module 6) --


class TestNoPIIExposure:
    """Intelligence endpoint must not leak PII or session IDs."""

    def test_compute_output_has_no_session_ids(self):
        """Compute result does not contain any session identifiers."""
        rows = [
            {"barrier_id": "credit", "resolved": True,
             "weeks_to_resolve": 4, "plan_accuracy": 3},
        ] * 5
        result = compute_calibrated_barriers(rows)
        dumped = result.model_dump()
        json_str = json.dumps(dumped)
        # No session_id, no individual feedback, no names
        assert "session_id" not in json_str
        assert "session" not in json_str.lower()

    def test_barrier_output_is_aggregate_only(self):
        """Each CalibratedBarrier contains only aggregate stats."""
        rows = [
            {"barrier_id": "credit", "resolved": True,
             "weeks_to_resolve": 4, "plan_accuracy": 3},
        ] * 5
        result = compute_calibrated_barriers(rows)
        for b in result.barriers:
            fields = set(type(b).model_fields.keys())
            expected = {
                "barrier_id", "avg_weeks", "stddev_weeks",
                "success_rate", "sample_size", "confidence",
            }
            assert fields == expected
