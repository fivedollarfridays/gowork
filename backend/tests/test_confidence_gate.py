"""Tests for the match confidence gate (Pattern 15)."""

from __future__ import annotations

from dataclasses import dataclass

from app.modules.matching.confidence_gate import (
    HIGH_THRESHOLD,
    MAYBE_THRESHOLD,
    MODERATE_THRESHOLD,
    classify_confidence,
)


@dataclass
class _FakeMatch:
    relevance_score: float


class TestClassifyConfidence:
    def test_no_matches_yields_no_match_tier(self) -> None:
        v = classify_confidence([])
        assert v.tier == "no_match"
        assert v.match_count == 0
        assert v.top_score == 0.0
        assert "Workforce Solutions" in v.recommended_action

    def test_top_below_maybe_threshold_yields_no_match(self) -> None:
        matches = [_FakeMatch(relevance_score=MAYBE_THRESHOLD - 0.05)]
        v = classify_confidence(matches)
        assert v.tier == "no_match"
        assert v.match_count == 1

    def test_maybe_tier(self) -> None:
        matches = [_FakeMatch(relevance_score=0.40)]
        v = classify_confidence(matches)
        assert v.tier == "maybe"
        assert "maybe match" in v.message
        assert "Workforce Solutions" in v.recommended_action

    def test_moderate_tier(self) -> None:
        matches = [_FakeMatch(relevance_score=0.55)]
        v = classify_confidence(matches)
        assert v.tier == "moderate"
        assert "promising" in v.message
        # Moderate -> apply but verify
        assert "WSTC" in v.recommended_action

    def test_high_tier(self) -> None:
        matches = [_FakeMatch(relevance_score=0.75)]
        v = classify_confidence(matches)
        assert v.tier == "high"
        assert "strong match" in v.message
        assert "Apply" in v.recommended_action

    def test_dict_match_shape_supported(self) -> None:
        """Plain dict matches also work."""
        matches = [{"relevance_score": 0.70, "title": "CNA"}]
        v = classify_confidence(matches)
        assert v.tier == "high"

    def test_threshold_boundary_high_inclusive(self) -> None:
        """Score exactly at HIGH_THRESHOLD -> high tier."""
        matches = [_FakeMatch(relevance_score=HIGH_THRESHOLD)]
        v = classify_confidence(matches)
        assert v.tier == "high"

    def test_threshold_boundary_moderate(self) -> None:
        matches = [_FakeMatch(relevance_score=MODERATE_THRESHOLD)]
        v = classify_confidence(matches)
        assert v.tier == "moderate"

    def test_only_top_match_drives_tier(self) -> None:
        """Lower-ranked matches don't change the verdict."""
        matches = [
            _FakeMatch(relevance_score=0.80),
            _FakeMatch(relevance_score=0.20),
            _FakeMatch(relevance_score=0.10),
        ]
        v = classify_confidence(matches)
        assert v.tier == "high"
        assert v.match_count == 3
