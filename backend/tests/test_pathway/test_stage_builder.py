"""Tests for stage builder -- constructs pathway stages from barriers + wages."""

import pytest

from app.modules.pathway.types import PathwayStep


class TestBuildStages:
    """Build pathway stages by fusing barrier sequence with wage targets."""

    def test_single_barrier_single_stage(self):
        from app.modules.pathway.stage_builder import build_stages

        stages = build_stages(
            barrier_ids=["criminal_record"],
            wage_targets=[12.0, 18.0],
            jobs_per_wage={12.0: 5, 18.0: 10},
        )
        assert len(stages) >= 1
        assert stages[0].stage == 1
        assert isinstance(stages[0], PathwayStep)

    def test_multiple_barriers_ordered_by_sequence(self):
        from app.modules.pathway.stage_builder import build_stages

        stages = build_stages(
            barrier_ids=["CREDIT_LOW_SCORE", "HOUSING_UNSTABLE"],
            wage_targets=[12.0, 16.0, 20.0],
            jobs_per_wage={12.0: 3, 16.0: 7, 20.0: 12},
        )
        # CREDIT_LOW_SCORE CAUSES HOUSING_UNSTABLE, so credit first
        assert len(stages) >= 2
        # First stage should have lowest wage target
        assert stages[0].target_wage <= stages[-1].target_wage

    def test_stages_have_cumulative_weeks(self):
        from app.modules.pathway.stage_builder import build_stages

        stages = build_stages(
            barrier_ids=["criminal_record", "transportation"],
            wage_targets=[10.0, 14.0, 18.0],
            jobs_per_wage={10.0: 2, 14.0: 5, 18.0: 8},
        )
        # Weeks should be non-decreasing
        weeks = [s.estimated_weeks for s in stages]
        assert weeks == sorted(weeks)

    def test_no_barriers_still_produces_stages(self):
        from app.modules.pathway.stage_builder import build_stages

        stages = build_stages(
            barrier_ids=[],
            wage_targets=[12.0, 18.0],
            jobs_per_wage={12.0: 5, 18.0: 10},
        )
        # Should still have wage progression stages
        assert len(stages) >= 1

    def test_stage_titles_are_descriptive(self):
        from app.modules.pathway.stage_builder import build_stages

        stages = build_stages(
            barrier_ids=["criminal_record"],
            wage_targets=[12.0, 20.0],
            jobs_per_wage={12.0: 4, 20.0: 9},
        )
        for stage in stages:
            assert len(stage.title) > 0
            assert stage.title != ""


class TestWageTierLabels:
    """Wage tiers should have meaningful labels."""

    def test_low_wage_label(self):
        from app.modules.pathway.stage_builder import wage_tier_label

        label = wage_tier_label(8.0)
        assert "entry" in label.lower()

    def test_mid_wage_label(self):
        from app.modules.pathway.stage_builder import wage_tier_label

        label = wage_tier_label(15.0)
        assert len(label) > 0

    def test_high_wage_label(self):
        from app.modules.pathway.stage_builder import wage_tier_label

        label = wage_tier_label(22.0)
        assert "skilled" in label.lower() or "career" in label.lower()
