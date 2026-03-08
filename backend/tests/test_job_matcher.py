"""Tests for job matcher types and keyword maps."""

import pytest

from app.modules.matching.types import JobMatch, MatchBucket, ScoredJobMatch


class TestMatchBucket:
    def test_has_strong_value(self):
        assert MatchBucket.STRONG == "strong"

    def test_has_possible_value(self):
        assert MatchBucket.POSSIBLE == "possible"

    def test_has_after_repair_value(self):
        assert MatchBucket.AFTER_REPAIR == "after_repair"


class TestScoredJobMatch:
    def test_extends_job_match(self):
        assert issubclass(ScoredJobMatch, JobMatch)

    def test_constructible_with_required_fields(self):
        m = ScoredJobMatch(
            title="CNA",
            relevance_score=0.85,
            match_reason="Matches your CNA experience",
            bucket="strong",
        )
        assert m.title == "CNA"
        assert m.relevance_score == 0.85
        assert m.match_reason == "Matches your CNA experience"
        assert m.bucket == "strong"

    def test_inherits_job_match_defaults(self):
        m = ScoredJobMatch(
            title="CNA",
            relevance_score=0.5,
            match_reason="General match",
            bucket="possible",
        )
        assert m.eligible_now is True
        assert m.credit_check_required == "unknown"

    def test_score_clamped_to_range(self):
        """relevance_score should be between 0.0 and 1.0."""
        m = ScoredJobMatch(
            title="Test",
            relevance_score=0.0,
            match_reason="Low",
            bucket="possible",
        )
        assert m.relevance_score == 0.0

        m2 = ScoredJobMatch(
            title="Test",
            relevance_score=1.0,
            match_reason="High",
            bucket="strong",
        )
        assert m2.relevance_score == 1.0


class TestIndustryKeywords:
    def test_covers_seven_industries(self):
        from app.modules.matching.job_keywords import INDUSTRY_KEYWORDS

        expected = {
            "healthcare", "manufacturing", "food_service",
            "government", "retail", "construction", "transportation",
        }
        assert set(INDUSTRY_KEYWORDS.keys()) == expected

    def test_each_industry_has_keywords(self):
        from app.modules.matching.job_keywords import INDUSTRY_KEYWORDS

        for industry, keywords in INDUSTRY_KEYWORDS.items():
            assert len(keywords) >= 3, f"{industry} has too few keywords"


class TestScheduleConflictKeywords:
    def test_has_daytime_and_evening(self):
        from app.modules.matching.job_keywords import SCHEDULE_CONFLICT_KEYWORDS

        assert "daytime" in SCHEDULE_CONFLICT_KEYWORDS
        assert "evening" in SCHEDULE_CONFLICT_KEYWORDS

    def test_each_schedule_has_keywords(self):
        from app.modules.matching.job_keywords import SCHEDULE_CONFLICT_KEYWORDS

        for stype, keywords in SCHEDULE_CONFLICT_KEYWORDS.items():
            assert len(keywords) >= 2, f"{stype} has too few conflict keywords"


class TestSkillsStopWords:
    def test_is_non_empty_set(self):
        from app.modules.matching.job_keywords import SKILLS_STOP_WORDS

        assert isinstance(SKILLS_STOP_WORDS, set)
        assert len(SKILLS_STOP_WORDS) >= 5


@pytest.mark.anyio
async def test_match_jobs_full_pipeline(test_engine):
    """Exercise the full match_jobs pipeline with DB data (covers lines 15, 105-116)."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from app.modules.matching.job_matcher import match_jobs
    from app.modules.matching.types import (
        BarrierSeverity,
        BarrierType,
        EmploymentStatus,
        UserProfile,
    )

    factory = async_sessionmaker(test_engine, class_=AsyncSession)
    async with factory() as session:
        await session.execute(text(
            "INSERT INTO job_listings "
            "(title, company, location, description, url, source, scraped_at, credit_check) "
            "VALUES ('CNA', 'Baptist Hospital', 'Montgomery, AL', "
            "'Certified Nursing Assistant needed', "
            "'http://example.com', 'test', '2026-03-07', 'unknown')"
        ))
        await session.execute(text(
            "INSERT INTO transit_stops (stop_name, lat, lng, sequence) "
            "VALUES ('Downtown', 32.375, -86.296, 1)"
        ))
        await session.commit()

        profile = UserProfile(
            session_id="test-session",
            zip_code="36104",
            employment_status=EmploymentStatus.UNEMPLOYED,
            barrier_count=1,
            primary_barriers=[BarrierType.CREDIT],
            barrier_severity=BarrierSeverity.LOW,
            needs_credit_assessment=True,
            transit_dependent=True,
            schedule_type="daytime",
            work_history="Former CNA at hospital",
            target_industries=["healthcare"],
        )

        ranked = await match_jobs(profile, session)
        assert len(ranked) >= 1
        assert ranked[0].title == "CNA"
