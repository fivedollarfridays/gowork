"""Tests for pathway type models -- RED phase."""

import pytest
from pydantic import ValidationError


class TestPathwayStep:
    """A pathway step represents one stage of a career trajectory."""

    def test_step_has_required_fields(self):
        from app.modules.pathway.types import PathwayStep

        step = PathwayStep(
            stage=1,
            title="Entry-level warehouse",
            target_wage=12.0,
            barriers_to_resolve=["criminal_record"],
            estimated_weeks=0,
            jobs_accessible=5,
        )
        assert step.stage == 1
        assert step.target_wage == 12.0
        assert step.barriers_to_resolve == ["criminal_record"]
        assert step.estimated_weeks == 0
        assert step.jobs_accessible == 5

    def test_step_has_cliff_warning(self):
        from app.modules.pathway.types import CliffWarning, PathwayStep

        warning = CliffWarning(
            program="SNAP",
            cliff_wage=16.50,
            monthly_loss=180.0,
            severity="moderate",
        )
        step = PathwayStep(
            stage=2,
            title="Logistics coordinator",
            target_wage=18.0,
            barriers_to_resolve=[],
            estimated_weeks=12,
            jobs_accessible=10,
            cliff_warnings=[warning],
        )
        assert len(step.cliff_warnings) == 1
        assert step.cliff_warnings[0].program == "SNAP"
        assert step.cliff_warnings[0].cliff_wage == 16.50

    def test_step_has_net_monthly_income(self):
        from app.modules.pathway.types import PathwayStep

        step = PathwayStep(
            stage=1,
            title="Warehouse",
            target_wage=12.0,
            barriers_to_resolve=[],
            estimated_weeks=0,
            jobs_accessible=3,
            net_monthly_income=1650.0,
        )
        assert step.net_monthly_income == 1650.0

    def test_step_defaults(self):
        from app.modules.pathway.types import PathwayStep

        step = PathwayStep(
            stage=1,
            title="Entry",
            target_wage=10.0,
            barriers_to_resolve=[],
            estimated_weeks=0,
            jobs_accessible=0,
        )
        assert step.cliff_warnings == []
        assert step.net_monthly_income is None
        assert step.unlocked_programs == []


class TestCareerPathway:
    """A career pathway is a sequence of steps from current state to target."""

    def test_pathway_has_steps_and_metadata(self):
        from app.modules.pathway.types import CareerPathway, PathwayStep

        steps = [
            PathwayStep(
                stage=1, title="Start", target_wage=12.0,
                barriers_to_resolve=[], estimated_weeks=0, jobs_accessible=3,
            ),
            PathwayStep(
                stage=2, title="Advance", target_wage=18.0,
                barriers_to_resolve=["criminal_record"], estimated_weeks=12,
                jobs_accessible=8,
            ),
        ]
        pathway = CareerPathway(
            pathway_id="warehouse-to-logistics",
            name="Warehouse to Logistics",
            steps=steps,
            total_weeks=12,
            final_wage=18.0,
            final_net_monthly=2400.0,
            viability_score=0.75,
        )
        assert len(pathway.steps) == 2
        assert pathway.total_weeks == 12
        assert pathway.final_wage == 18.0
        assert pathway.viability_score == 0.75

    def test_pathway_viability_score_clamped(self):
        from app.modules.pathway.types import CareerPathway, PathwayStep

        step = PathwayStep(
            stage=1, title="X", target_wage=10.0,
            barriers_to_resolve=[], estimated_weeks=0, jobs_accessible=1,
        )
        with pytest.raises(ValidationError):
            CareerPathway(
                pathway_id="bad", name="Bad", steps=[step],
                total_weeks=0, final_wage=10.0,
                final_net_monthly=1000.0, viability_score=1.5,
            )


class TestPathwayResult:
    """The pathway result contains multiple ranked pathways."""

    def test_result_contains_pathways(self):
        from app.modules.pathway.types import CareerPathway, PathwayResult, PathwayStep

        step = PathwayStep(
            stage=1, title="Start", target_wage=12.0,
            barriers_to_resolve=[], estimated_weeks=0, jobs_accessible=3,
        )
        pathway = CareerPathway(
            pathway_id="p1", name="Path A", steps=[step],
            total_weeks=0, final_wage=12.0, final_net_monthly=1650.0,
            viability_score=0.8,
        )
        result = PathwayResult(
            pathways=[pathway],
            current_wage=0.0,
            current_net_monthly=0.0,
            barriers_active=["criminal_record", "transportation"],
        )
        assert len(result.pathways) == 1
        assert result.barriers_active == ["criminal_record", "transportation"]

    def test_result_best_pathway_property(self):
        from app.modules.pathway.types import CareerPathway, PathwayResult, PathwayStep

        step = PathwayStep(
            stage=1, title="X", target_wage=10.0,
            barriers_to_resolve=[], estimated_weeks=0, jobs_accessible=1,
        )
        p1 = CareerPathway(
            pathway_id="p1", name="A", steps=[step], total_weeks=0,
            final_wage=10.0, final_net_monthly=1000.0, viability_score=0.6,
        )
        p2 = CareerPathway(
            pathway_id="p2", name="B", steps=[step], total_weeks=0,
            final_wage=15.0, final_net_monthly=1800.0, viability_score=0.9,
        )
        result = PathwayResult(
            pathways=[p1, p2], current_wage=0.0,
            current_net_monthly=0.0, barriers_active=[],
        )
        assert result.best_pathway.pathway_id == "p2"
