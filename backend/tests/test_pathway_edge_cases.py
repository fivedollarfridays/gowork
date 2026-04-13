"""Edge case tests for pathway module -- targeting uncovered lines.

Covers:
- cliff_navigator: unknown program (line 54), while-else recovery (line 101),
  is_wage_safe in-zone (line 119), no-targets fallback (lines 157-158)
- engine: severity_label mild (line 98), compute_viability empty steps (line 112)
- stage_builder: wage_tier_label fallback (line 30), empty wage targets (line 112)
- types: best_pathway with empty pathways (line 62)
"""

import pytest

from app.modules.benefits.types import BenefitsProfile
from app.modules.pathway.cliff_navigator import (
    CliffZone,
    find_cliff_zones,
    find_safe_wage_targets,
    is_wage_safe,
)
from app.modules.pathway.engine import (
    _compute_viability,
    _estimate_jobs_at_wage,
    _severity_label,
)
from app.modules.pathway.stage_builder import (
    _assign_barriers_to_stages,
    _compute_stage_weeks,
    build_stages,
    wage_tier_label,
)
from app.modules.pathway.types import (
    CareerPathway,
    PathwayResult,
    PathwayStep,
)


class TestCliffNavigatorEdgeCases:
    """Edge cases for cliff navigator."""

    def test_unknown_program_skipped(self):
        """Unknown program in enrolled_programs is silently skipped (line 54)."""
        profile = BenefitsProfile(
            household_size=3,
            annual_income=20000,
            enrolled_programs=["nonexistent_program"],
        )
        zones = find_cliff_zones(profile)
        # Unknown programs have no calculator, so no zones
        assert zones == []

    def test_is_wage_safe_inside_zone_returns_false(self):
        """Wage inside a cliff zone returns False (line 119)."""
        zone = CliffZone(
            program="SNAP",
            cliff_start=15.0,
            cliff_end=20.0,
            max_monthly_loss=150.0,
        )
        assert is_wage_safe(17.0, [zone]) is False

    def test_is_wage_safe_at_boundary_is_safe(self):
        """Wage at cliff_start or cliff_end is safe (not strictly inside)."""
        zone = CliffZone(
            program="SNAP",
            cliff_start=15.0,
            cliff_end=20.0,
            max_monthly_loss=150.0,
        )
        # At boundaries: cliff_start < wage < cliff_end (exclusive)
        assert is_wage_safe(15.0, [zone]) is True
        assert is_wage_safe(20.0, [zone]) is True

    def test_is_wage_safe_no_zones(self):
        """Any wage is safe with no cliff zones."""
        assert is_wage_safe(15.0, []) is True

    def test_find_safe_wage_targets_high_current_wage(self):
        """High current wage near WAGE_MAX triggers fallback (lines 157-158)."""
        profile = BenefitsProfile(
            household_size=1,
            annual_income=50000,
            enrolled_programs=[],
        )
        # Set current_wage very high so no safe targets found in normal range
        targets = find_safe_wage_targets(profile, current_wage=48.0, step_size=2.0)
        assert len(targets) >= 1
        # Should still return at least one target


class TestSeverityLabel:
    """_severity_label classification (lines 94-98)."""

    def test_severe(self):
        assert _severity_label(250.0) == "severe"

    def test_moderate(self):
        assert _severity_label(100.0) == "moderate"

    def test_mild(self):
        assert _severity_label(30.0) == "mild"

    def test_boundary_severe(self):
        assert _severity_label(200.0) == "severe"

    def test_boundary_moderate(self):
        assert _severity_label(50.0) == "moderate"

    def test_zero_loss(self):
        assert _severity_label(0.0) == "mild"


class TestComputeViability:
    """_compute_viability scoring (line 112 for empty steps)."""

    def test_empty_steps_returns_zero(self):
        assert _compute_viability([], barrier_count=3, total_weeks=12) == 0.0

    def test_normal_steps_returns_positive(self):
        step = PathwayStep(
            stage=1, title="Entry", target_wage=12.0,
            barriers_to_resolve=["credit"], estimated_weeks=8,
            jobs_accessible=10,
        )
        score = _compute_viability([step], barrier_count=1, total_weeks=8)
        assert 0.0 < score <= 1.0

    def test_many_barriers_reduces_viability(self):
        step = PathwayStep(
            stage=1, title="X", target_wage=12.0,
            barriers_to_resolve=[], estimated_weeks=4,
            jobs_accessible=5,
        )
        score_few = _compute_viability([step], barrier_count=1, total_weeks=4)
        score_many = _compute_viability([step], barrier_count=5, total_weeks=4)
        assert score_few > score_many

    def test_long_timeline_reduces_viability(self):
        step = PathwayStep(
            stage=1, title="X", target_wage=12.0,
            barriers_to_resolve=[], estimated_weeks=4,
            jobs_accessible=5,
        )
        score_short = _compute_viability([step], barrier_count=1, total_weeks=4)
        score_long = _compute_viability([step], barrier_count=1, total_weeks=60)
        assert score_short > score_long


class TestEstimateJobsAtWage:
    """_estimate_jobs_at_wage wage tiers and barrier penalties."""

    def test_low_wage_more_jobs(self):
        """Low wages ($10 or less) have highest base jobs."""
        assert _estimate_jobs_at_wage(8.0, []) == 15

    def test_mid_wage_fewer_jobs(self):
        """$14-18 has fewer base jobs."""
        jobs = _estimate_jobs_at_wage(16.0, [])
        assert jobs == 8

    def test_high_wage_fewest_jobs(self):
        """Above $22 has fewest base jobs."""
        jobs = _estimate_jobs_at_wage(25.0, [])
        assert jobs == 3

    def test_barriers_reduce_jobs(self):
        """Active barriers reduce accessible job count."""
        no_barriers = _estimate_jobs_at_wage(12.0, [])
        with_barriers = _estimate_jobs_at_wage(12.0, ["criminal_record", "credit"])
        assert with_barriers < no_barriers

    def test_unknown_barrier_uses_default_penalty(self):
        """Unknown barriers use 0.9 penalty."""
        known = _estimate_jobs_at_wage(12.0, ["criminal_record"])
        unknown = _estimate_jobs_at_wage(12.0, ["unknown_barrier"])
        # criminal_record has 0.6 penalty, unknown has 0.9, so unknown has more jobs
        assert unknown > known

    def test_minimum_one_job(self):
        """Even with heavy penalties, at least 1 job is returned."""
        jobs = _estimate_jobs_at_wage(25.0, [
            "criminal_record", "credit", "transportation",
            "housing", "health", "training", "childcare",
        ])
        assert jobs >= 1


class TestWageTierLabelEdgeCases:
    """wage_tier_label edge cases."""

    def test_above_all_thresholds(self):
        """Wage above all thresholds returns advanced label (line 30)."""
        label = wage_tier_label(999.0)
        assert "advanced" in label.lower() or "career" in label.lower()

    def test_exactly_at_thresholds(self):
        """Wage exactly at threshold boundaries."""
        assert "entry" in wage_tier_label(10.0).lower()
        assert "stable" in wage_tier_label(13.0).lower()
        assert "mid" in wage_tier_label(16.0).lower()


class TestAssignBarriersToStages:
    """_assign_barriers_to_stages edge cases."""

    def test_empty_barriers_empty_stages(self):
        """No barriers: all stages get empty lists."""
        result = _assign_barriers_to_stages([], 3)
        assert len(result) == 3
        assert all(s == [] for s in result)

    def test_zero_stages(self):
        """Zero stages: returns at least one empty list."""
        result = _assign_barriers_to_stages(["credit"], 0)
        assert len(result) >= 1

    def test_more_barriers_than_stages(self):
        """More barriers than stages: later stages get multiple barriers."""
        result = _assign_barriers_to_stages(
            ["criminal_record", "credit", "housing", "health"], 2,
        )
        assert len(result) == 2
        # All barriers should be distributed
        all_assigned = [b for stage in result for b in stage]
        assert len(all_assigned) == 4


class TestComputeStageWeeks:
    """_compute_stage_weeks with and without calibration."""

    def test_known_barriers_use_defaults(self):
        weeks = _compute_stage_weeks(["criminal_record", "credit"])
        assert weeks > 0

    def test_unknown_barriers_use_fallback(self):
        weeks = _compute_stage_weeks(["unknown_barrier"])
        assert weeks == 4  # default fallback

    def test_calibrated_overrides_default(self):
        default = _compute_stage_weeks(["credit"])
        calibrated = _compute_stage_weeks(["credit"], calibrated_weeks={"credit": 2})
        assert calibrated == 2
        assert calibrated != default

    def test_empty_barriers_zero_weeks(self):
        assert _compute_stage_weeks([]) == 0


class TestBuildStagesEdgeCases:
    """build_stages edge cases."""

    def test_empty_wage_targets_returns_empty(self):
        """No wage targets: returns empty list (line 112)."""
        result = build_stages(
            barrier_ids=["credit"],
            wage_targets=[],
            jobs_per_wage={},
        )
        assert result == []


class TestPathwayResultBestPathway:
    """best_pathway computed property with empty pathways (line 62)."""

    def test_empty_pathways_returns_none(self):
        result = PathwayResult(
            pathways=[],
            current_wage=10.0,
            current_net_monthly=1500.0,
            barriers_active=["credit"],
        )
        assert result.best_pathway is None
