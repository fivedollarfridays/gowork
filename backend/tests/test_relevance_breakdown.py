"""Stage-2 enrichment: ``score_resume_match_breakdown`` exposes the
per-factor scores for UI consumption.

Lets the frontend render a "why this match" panel without recomputing
the score: the breakdown shape is locked here so client renderers can
rely on it.
"""

from __future__ import annotations

from app.modules.matching.relevance_scorer import (
    build_resume_profile,
    score_resume_match,
    score_resume_match_breakdown,
)


def _nurse_profile():
    return build_resume_profile(
        "Registered Nurse RN with 10 years critical care ICU experience. "
        "BLS ACLS PALS certifications. patient assessment EHR Epic. BSN."
    )


def _nurse_job() -> dict:
    return {
        "title": "Registered Nurse - Med Surg",
        "company": "JPS Health Network",
        "location": "Fort Worth, TX 76104",
        "description": (
            "RN role on med-surg unit. BSN preferred. BLS ACLS required. "
            "Pay: $34/hr."
        ),
    }


def _construction_job() -> dict:
    return {
        "title": "Construction Apprentice",
        "company": "JE Dunn Construction",
        "location": "Fort Worth, TX 76102",
        "description": (
            "Entry-level apprenticeship on commercial build sites across "
            "DFW. Learn carpentry, concrete, and site safety. OSHA-10 "
            "within 30 days."
        ),
    }


class TestScoreBreakdownShape:
    def test_returns_three_tuple(self) -> None:
        result = score_resume_match_breakdown(_nurse_job(), _nurse_profile())
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_breakdown_has_all_factor_keys(self) -> None:
        _, _, b = score_resume_match_breakdown(_nurse_job(), _nurse_profile())
        for key in (
            "skills", "title_family", "industry", "years",
            "education", "certifications", "industry_aligned",
        ):
            assert key in b, f"breakdown missing {key}"

    def test_factor_values_in_unit_range(self) -> None:
        _, _, b = score_resume_match_breakdown(_nurse_job(), _nurse_profile())
        for key, value in b.items():
            if key == "industry_aligned":
                assert isinstance(value, bool)
                continue
            assert 0.0 <= value <= 1.0, f"{key}={value} out of range"


class TestBreakdownReflectsAlignment:
    def test_aligned_match_scores_high_industry(self) -> None:
        _, _, b = score_resume_match_breakdown(_nurse_job(), _nurse_profile())
        assert b["industry_aligned"] is True
        assert b["industry"] == 1.0
        assert b["title_family"] == 1.0

    def test_misaligned_match_scores_low_industry(self) -> None:
        _, _, b = score_resume_match_breakdown(
            _construction_job(), _nurse_profile(),
        )
        assert b["industry_aligned"] is False
        assert b["industry"] == 0.0


class TestPublicAPIBackwardCompatible:
    """``score_resume_match`` keeps its (score, signals) return shape."""

    def test_two_tuple_unchanged(self) -> None:
        result = score_resume_match(_nurse_job(), _nurse_profile())
        assert isinstance(result, tuple)
        assert len(result) == 2
        score, signals = result
        assert isinstance(score, float)
        assert isinstance(signals, list)

    def test_score_matches_breakdown_score(self) -> None:
        score_pair = score_resume_match(_nurse_job(), _nurse_profile())[0]
        score_triple = score_resume_match_breakdown(
            _nurse_job(), _nurse_profile(),
        )[0]
        assert score_pair == score_triple
