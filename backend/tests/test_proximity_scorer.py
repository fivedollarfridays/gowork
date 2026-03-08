"""Tests for proximity scorer module."""

from app.modules.matching.proximity_scorer import extract_zip, score_proximity


class TestExtractZip:
    """Tests for zip code extraction from location strings."""

    def test_extracts_zip_from_full_address(self) -> None:
        result = extract_zip("7680 Eastchase Parkway, Montgomery, AL 36117")
        assert result == "36117"

    def test_returns_none_when_no_zip(self) -> None:
        result = extract_zip("Montgomery, AL")
        assert result is None

    def test_returns_none_for_empty_string(self) -> None:
        result = extract_zip("")
        assert result is None


class TestScoreProximityCoreDistance:
    """Tests for score_proximity distance-based scoring."""

    def test_same_zip_scores_max(self) -> None:
        """Same zip for user and job => 0 miles => 1.0."""
        score = score_proximity(
            "36117", "7680 Eastchase Parkway, Montgomery, AL 36117", False
        )
        assert score == 1.0

    def test_mid_range_distance(self) -> None:
        """36101 (downtown) to 36117 (east) is ~8mi => mid-range score."""
        score = score_proximity(
            "36101", "7680 Eastchase Parkway, Montgomery, AL 36117", False
        )
        assert 0.3 < score < 0.8

    def test_transit_penalty_lowers_score(self) -> None:
        """Transit-dependent should score lower than driving for same route."""
        driving = score_proximity(
            "36101", "7680 Eastchase Parkway, Montgomery, AL 36117", False
        )
        transit = score_proximity(
            "36101", "7680 Eastchase Parkway, Montgomery, AL 36117", True
        )
        assert transit < driving


class TestScoreProximityFallbacks:
    """Tests for fallback and edge-case behavior."""

    def test_unknown_job_zip_uses_downtown_fallback(self) -> None:
        """Job zip 99999 not in centroids => falls back to downtown."""
        score = score_proximity(
            "36101", "123 Fake St, Montgomery, AL 99999", False
        )
        # 36101 IS downtown, so distance ~0 => score ~1.0
        assert score == 1.0

    def test_no_zip_in_job_location_uses_downtown(self) -> None:
        """No zip in job location string => falls back to downtown."""
        score = score_proximity("36101", "Montgomery, AL", False)
        # 36101 IS downtown, so distance ~0 => score ~1.0
        assert score == 1.0

    def test_large_distance_scores_minimum(self) -> None:
        """Distance >= 15mi should score 0.1."""
        # 36117 is east (~8mi from downtown).  Use a user zip far away.
        # We use 36116 (south) to 36117 (east) which is ~7mi, not enough.
        # Instead, test _distance_to_score directly for 15+ miles.
        from app.modules.matching.proximity_scorer import _distance_to_score

        assert _distance_to_score(15.0) == 0.1
        assert _distance_to_score(20.0) == 0.1
        assert _distance_to_score(100.0) == 0.1

    def test_very_close_distance_scores_max(self) -> None:
        """Distance <= 1mi should score 1.0."""
        from app.modules.matching.proximity_scorer import _distance_to_score

        assert _distance_to_score(0.0) == 1.0
        assert _distance_to_score(0.5) == 1.0
        assert _distance_to_score(1.0) == 1.0
