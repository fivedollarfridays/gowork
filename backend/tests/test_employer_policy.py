"""Tests for employer policy — T26.2.

Tests cover:
- EmployerPolicy model validation + defaults
- matches_record() eligibility logic
- query_eligible_employers() filtering + sorting
- DB round-trip (table exists, seed idempotency)
"""

import pytest

from app.modules.criminal.employer_policy import (
    EmployerPolicy,
    matches_record,
    query_eligible_employers,
)
from app.modules.criminal.record_profile import (
    ChargeCategory,
    RecordProfile,
    RecordType,
)


class TestEmployerPolicyModel:
    def test_default_values(self):
        """EmployerPolicy should have sensible defaults."""
        policy = EmployerPolicy(employer_name="Test Corp")
        assert policy.employer_name == "Test Corp"
        assert policy.fair_chance is False
        assert policy.excluded_charges == []
        assert policy.lookback_years is None
        assert policy.background_check_timing == "pre_offer"
        assert policy.industry is None
        assert policy.source is None
        assert policy.montgomery_area is True

    def test_full_policy(self):
        """All fields populated."""
        policy = EmployerPolicy(
            employer_name="Fair Corp",
            fair_chance=True,
            excluded_charges=["violence", "sex_offense"],
            lookback_years=7,
            background_check_timing="post_offer",
            industry="retail",
            source="company_website",
            montgomery_area=True,
        )
        assert policy.fair_chance is True
        assert "violence" in policy.excluded_charges
        assert policy.lookback_years == 7
        assert policy.background_check_timing == "post_offer"
        assert policy.industry == "retail"

    def test_serialization_round_trip(self):
        """Model -> JSON -> Model round-trip."""
        import json

        original = EmployerPolicy(
            employer_name="Round Trip LLC",
            fair_chance=True,
            excluded_charges=["fraud"],
            lookback_years=5,
        )
        data = json.loads(original.model_dump_json())
        restored = EmployerPolicy(**data)
        assert restored == original


class TestMatchesRecord:
    def test_expunged_matches_all(self):
        """Expunged records should match any employer."""
        policy = EmployerPolicy(
            employer_name="Strict Corp",
            excluded_charges=["violence", "theft", "drug"],
            lookback_years=3,
        )
        profile = RecordProfile(
            record_types=[RecordType.EXPUNGED],
            charge_categories=[ChargeCategory.VIOLENCE],
            years_since_conviction=1,
        )
        assert matches_record(policy, profile) is True

    def test_excluded_charge_blocks(self):
        """Employer excluding violence should reject violence charges."""
        policy = EmployerPolicy(
            employer_name="No Violence Inc",
            excluded_charges=["violence"],
        )
        profile = RecordProfile(
            record_types=[RecordType.FELONY],
            charge_categories=[ChargeCategory.VIOLENCE],
            years_since_conviction=10,
            completed_sentence=True,
        )
        assert matches_record(policy, profile) is False

    def test_lookback_window_blocks(self):
        """Conviction within lookback window should be rejected."""
        policy = EmployerPolicy(
            employer_name="7yr Lookback Corp",
            lookback_years=7,
        )
        profile = RecordProfile(
            record_types=[RecordType.MISDEMEANOR],
            charge_categories=[ChargeCategory.THEFT],
            years_since_conviction=3,
        )
        assert matches_record(policy, profile) is False

    def test_lookback_window_passes(self):
        """Conviction beyond lookback window should pass."""
        policy = EmployerPolicy(
            employer_name="7yr Lookback Corp",
            lookback_years=7,
        )
        profile = RecordProfile(
            record_types=[RecordType.MISDEMEANOR],
            charge_categories=[ChargeCategory.THEFT],
            years_since_conviction=10,
        )
        assert matches_record(policy, profile) is True

    def test_no_restrictions_matches_all(self):
        """Policy with no excluded charges and no lookback matches anyone."""
        policy = EmployerPolicy(
            employer_name="Open Door LLC",
            fair_chance=True,
        )
        profile = RecordProfile(
            record_types=[RecordType.FELONY],
            charge_categories=[ChargeCategory.VIOLENCE],
            years_since_conviction=1,
        )
        assert matches_record(policy, profile) is True

    def test_empty_profile_matches_all(self):
        """Empty record profile should match any employer."""
        policy = EmployerPolicy(
            employer_name="Strict Corp",
            excluded_charges=["violence"],
            lookback_years=5,
        )
        profile = RecordProfile()
        assert matches_record(policy, profile) is True

    def test_no_years_since_conviction_with_lookback(self):
        """If years_since_conviction is None, lookback should not block."""
        policy = EmployerPolicy(
            employer_name="Lookback Corp",
            lookback_years=7,
        )
        profile = RecordProfile(
            record_types=[RecordType.FELONY],
            charge_categories=[ChargeCategory.DRUG],
        )
        assert matches_record(policy, profile) is True


_POLICIES = [
    EmployerPolicy(employer_name="Fair Corp", fair_chance=True),
    EmployerPolicy(
        employer_name="Strict Corp",
        excluded_charges=["violence", "sex_offense"],
        lookback_years=7,
    ),
    EmployerPolicy(
        employer_name="Medium Corp",
        excluded_charges=["sex_offense"],
        lookback_years=5,
    ),
    EmployerPolicy(employer_name="Open LLC", fair_chance=True),
]


class TestQueryEligibleEmployers:
    def test_filters_excluded_charges(self):
        """Should filter out employers whose exclusions match."""
        profile = RecordProfile(
            record_types=[RecordType.FELONY],
            charge_categories=[ChargeCategory.VIOLENCE],
            years_since_conviction=10,
        )
        result = query_eligible_employers(_POLICIES, profile)
        names = [p.employer_name for p in result]
        assert "Strict Corp" not in names
        assert "Fair Corp" in names
        assert "Medium Corp" in names

    def test_fair_chance_sorted_first(self):
        """Fair-chance employers should appear before non-fair-chance."""
        profile = RecordProfile(
            record_types=[RecordType.MISDEMEANOR],
            charge_categories=[ChargeCategory.THEFT],
            years_since_conviction=10,
        )
        result = query_eligible_employers(_POLICIES, profile)
        # First results should be fair_chance=True
        assert result[0].fair_chance is True
        assert result[1].fair_chance is True

    def test_expunged_sees_all(self):
        """Expunged profile should see all employers."""
        profile = RecordProfile(record_types=[RecordType.EXPUNGED])
        result = query_eligible_employers(_POLICIES, profile)
        assert len(result) == len(_POLICIES)

    def test_empty_policies_list(self):
        """Empty policies list returns empty result."""
        profile = RecordProfile(record_types=[RecordType.FELONY])
        result = query_eligible_employers([], profile)
        assert result == []

    def test_lookback_filters_recent(self):
        """Recent convictions should be filtered by lookback."""
        profile = RecordProfile(
            record_types=[RecordType.MISDEMEANOR],
            charge_categories=[ChargeCategory.DRUG],
            years_since_conviction=3,
        )
        result = query_eligible_employers(_POLICIES, profile)
        names = [p.employer_name for p in result]
        assert "Strict Corp" not in names  # 7yr lookback, 3yr ago
        assert "Medium Corp" not in names  # 5yr lookback, 3yr ago
        assert "Fair Corp" in names
        assert "Open LLC" in names


# ---------------------------------------------------------------------------
# Database round-trip tests
# ---------------------------------------------------------------------------

class TestEmployerPolicyDB:
    @pytest.mark.anyio
    async def test_table_exists(self, test_engine):
        """employer_policies table should be created by DDL."""
        from sqlalchemy import text
        from app.core.database import get_async_session_factory

        factory = get_async_session_factory()
        async with factory() as session:
            result = await session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='employer_policies'")
            )
            assert result.scalar() == "employer_policies"

    @pytest.mark.anyio
    async def test_get_all_employer_policies(self, test_engine):
        """get_all_employer_policies should return rows from DB."""
        from sqlalchemy import text
        from app.core.database import get_async_session_factory
        from app.modules.criminal.queries import get_all_employer_policies

        factory = get_async_session_factory()
        async with factory() as session:
            await session.execute(text(
                "INSERT INTO employer_policies "
                "(employer_name, fair_chance, excluded_charges, lookback_years, "
                "bg_check_timing, industry, source, montgomery_area) "
                "VALUES ('Test Corp', 1, '[]', 5, 'post_offer', 'retail', 'web', 1)"
            ))
            await session.commit()
            result = await get_all_employer_policies(session)

        assert len(result) >= 1
        assert any(p.employer_name == "Test Corp" for p in result)

    @pytest.mark.anyio
    async def test_get_employer_policy_by_name(self, test_engine):
        """get_employer_policy_by_name should return specific employer."""
        from sqlalchemy import text
        from app.core.database import get_async_session_factory
        from app.modules.criminal.queries import get_employer_policy_by_name

        factory = get_async_session_factory()
        async with factory() as session:
            await session.execute(text(
                "INSERT INTO employer_policies "
                "(employer_name, fair_chance, excluded_charges, lookback_years, "
                "bg_check_timing, industry, source, montgomery_area) "
                "VALUES ('Unique Corp', 1, '[\"violence\"]', 7, 'pre_offer', 'food', 'manual', 1)"
            ))
            await session.commit()
            result = await get_employer_policy_by_name(session, "Unique Corp")

        assert result is not None
        assert result.employer_name == "Unique Corp"
        assert result.fair_chance is True
        assert "violence" in result.excluded_charges
        assert result.lookback_years == 7

    @pytest.mark.anyio
    async def test_get_nonexistent_returns_none(self, test_engine):
        """Getting a non-existent employer returns None."""
        from app.core.database import get_async_session_factory
        from app.modules.criminal.queries import get_employer_policy_by_name

        factory = get_async_session_factory()
        async with factory() as session:
            result = await get_employer_policy_by_name(session, "Ghost Corp")
        assert result is None


# ---------------------------------------------------------------------------
# Seed data tests
# ---------------------------------------------------------------------------

class TestEmployerPolicySeedMissingFile:
    @pytest.mark.anyio
    async def test_seed_missing_file_does_not_crash(self, test_engine):
        """When seed file is absent, seed_employer_policies logs warning and returns."""
        from unittest.mock import patch
        from pathlib import Path
        import tempfile

        from app.core.database import get_async_session_factory
        from app.modules.criminal.employer_seed import seed_employer_policies

        factory = get_async_session_factory()
        async with factory() as session:
            with patch("app.modules.criminal.employer_seed.resolve_data_dir") as mock_dir:
                empty_dir = Path(tempfile.mkdtemp())
                mock_dir.return_value = empty_dir
                # Should not raise
                await seed_employer_policies(session)


class TestEmployerPolicySeed:
    @pytest.mark.anyio
    async def test_seed_data_loads(self, test_engine):
        """Employer policy seed data should load into DB."""
        from app.core.database import get_async_session_factory
        from app.modules.criminal.employer_seed import seed_employer_policies

        factory = get_async_session_factory()
        async with factory() as session:
            await seed_employer_policies(session)
            from app.modules.criminal.queries import get_all_employer_policies
            result = await get_all_employer_policies(session)

        assert len(result) >= 20

    @pytest.mark.anyio
    async def test_seed_is_idempotent(self, test_engine):
        """Running seed twice should not duplicate rows."""
        from app.core.database import get_async_session_factory
        from app.modules.criminal.employer_seed import seed_employer_policies

        factory = get_async_session_factory()
        async with factory() as session:
            await seed_employer_policies(session)
            await seed_employer_policies(session)
            from app.modules.criminal.queries import get_all_employer_policies
            result = await get_all_employer_policies(session)

        # Should not have duplicates
        names = [p.employer_name for p in result]
        assert len(names) == len(set(names))

    @pytest.mark.anyio
    async def test_seed_covers_industries(self, test_engine):
        """Seed data should cover at least 5 industries."""
        from app.core.database import get_async_session_factory
        from app.modules.criminal.employer_seed import seed_employer_policies

        factory = get_async_session_factory()
        async with factory() as session:
            await seed_employer_policies(session)
            from app.modules.criminal.queries import get_all_employer_policies
            result = await get_all_employer_policies(session)

        industries = {p.industry for p in result if p.industry}
        assert len(industries) >= 5

    @pytest.mark.anyio
    async def test_seed_has_fair_chance_employers(self, test_engine):
        """Seed data should have at least 10 fair-chance employers."""
        from app.core.database import get_async_session_factory
        from app.modules.criminal.employer_seed import seed_employer_policies

        factory = get_async_session_factory()
        async with factory() as session:
            await seed_employer_policies(session)
            from app.modules.criminal.queries import get_all_employer_policies
            result = await get_all_employer_policies(session)

        fair_chance_count = sum(1 for p in result if p.fair_chance)
        assert fair_chance_count >= 10
