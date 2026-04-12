"""Tests for cliff navigator -- finds safe wage transitions."""

import pytest

from app.modules.benefits.types import BenefitsProfile


class TestFindCliffZones:
    """Identify wage ranges where benefits cliffs occur."""

    def test_snap_has_cliff_zone(self, snap_profile: BenefitsProfile):
        from app.modules.pathway.cliff_navigator import find_cliff_zones

        zones = find_cliff_zones(snap_profile)
        assert len(zones) >= 1
        # SNAP cliff should be somewhere in the wage range
        snap_zone = next((z for z in zones if z.program == "SNAP"), None)
        assert snap_zone is not None
        assert snap_zone.cliff_start > 0
        assert snap_zone.cliff_end >= snap_zone.cliff_start

    def test_no_programs_no_zones(self, no_benefits_profile: BenefitsProfile):
        from app.modules.pathway.cliff_navigator import find_cliff_zones

        zones = find_cliff_zones(no_benefits_profile)
        assert zones == []

    def test_multi_program_has_multiple_zones(
        self, multi_program_profile: BenefitsProfile,
    ):
        from app.modules.pathway.cliff_navigator import find_cliff_zones

        zones = find_cliff_zones(multi_program_profile)
        assert len(zones) >= 2


class TestIsWageSafe:
    """Check if a target wage avoids all cliff zones."""

    def test_low_wage_is_safe(self, snap_profile: BenefitsProfile):
        from app.modules.pathway.cliff_navigator import find_cliff_zones, is_wage_safe

        zones = find_cliff_zones(snap_profile)
        # $8/hr should be below any cliff
        assert is_wage_safe(8.0, zones) is True

    def test_high_wage_past_recovery_is_safe(
        self, snap_profile: BenefitsProfile,
    ):
        from app.modules.pathway.cliff_navigator import find_cliff_zones, is_wage_safe

        zones = find_cliff_zones(snap_profile)
        # $25/hr should be past any recovery wage
        assert is_wage_safe(25.0, zones) is True


class TestFindSafeWageTargets:
    """Find wages that are safe landing points for career steps."""

    def test_returns_ascending_wages(self, snap_profile: BenefitsProfile):
        from app.modules.pathway.cliff_navigator import find_safe_wage_targets

        targets = find_safe_wage_targets(snap_profile, current_wage=8.0)
        assert len(targets) >= 1
        # Each target should be > current wage
        for t in targets:
            assert t.wage > 8.0
        # Should be ascending
        wages = [t.wage for t in targets]
        assert wages == sorted(wages)

    def test_each_target_has_net_income(self, snap_profile: BenefitsProfile):
        from app.modules.pathway.cliff_navigator import find_safe_wage_targets

        targets = find_safe_wage_targets(snap_profile, current_wage=8.0)
        for t in targets:
            assert t.net_monthly > 0
            assert t.wage > 0

    def test_no_programs_still_returns_targets(
        self, no_benefits_profile: BenefitsProfile,
    ):
        from app.modules.pathway.cliff_navigator import find_safe_wage_targets

        targets = find_safe_wage_targets(no_benefits_profile, current_wage=8.0)
        # Even without programs, should suggest wage targets
        assert len(targets) >= 1
