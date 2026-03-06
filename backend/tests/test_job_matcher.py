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
