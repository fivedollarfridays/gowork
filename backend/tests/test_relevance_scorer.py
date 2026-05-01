"""Tests for resume-vs-job semantic relevance scoring.

The relevance scorer is the missing piece that produced
"0.363 for everyone" before this change: the previous PVS only
considered proximity / time_fit / barrier_compat, none of which
vary across same-city jobs without a ZIP-bearing resume signal.

These tests pin the contract for the new ``score_resume_match``
helper and the wiring through ``ScoringContext.resume_keywords``.
"""

from app.modules.matching.relevance_scorer import (
    ResumeProfile,
    build_resume_profile,
    score_resume_match,
)


def _job(**overrides: object) -> dict:
    base: dict[str, object] = {
        "title": "Cashier",
        "company": "Store",
        "location": "Fort Worth, TX 76102",
        "description": "Light retail work. Greet customers, ring up purchases.",
    }
    base.update(overrides)
    return base


class TestBuildResumeProfile:
    """build_resume_profile turns raw text into a ResumeProfile."""

    def test_empty_text_returns_empty_profile(self) -> None:
        profile = build_resume_profile("")
        assert profile.skills == []
        assert profile.industries == []
        assert profile.years_experience == 0
        assert profile.certifications == []

    def test_extracts_nursing_signals(self) -> None:
        text = (
            "Registered Nurse with 10 years of ICU experience. "
            "BLS certified. ACLS certified. Epic EHR. Cared for "
            "post-op patients in critical care."
        )
        profile = build_resume_profile(text)
        assert "nurse" in profile.skills or "nursing" in profile.skills
        assert "healthcare" in profile.industries
        assert profile.years_experience >= 10
        assert "BLS" in profile.certifications
        assert "ACLS" in profile.certifications

    def test_extracts_logistics_signals(self) -> None:
        text = (
            "Forklift operator with 5 years warehouse experience. "
            "OSHA-10 certified. Loaded and unloaded freight. CDL-A holder."
        )
        profile = build_resume_profile(text)
        assert "forklift" in profile.skills
        assert "manufacturing" in profile.industries or "transportation" in profile.industries
        assert profile.years_experience >= 5
        assert "CDL" in profile.certifications

    def test_extracts_construction_signals(self) -> None:
        text = (
            "Welder with 7 years experience on commercial sites. "
            "Carpentry, concrete forming. OSHA-30."
        )
        profile = build_resume_profile(text)
        assert profile.years_experience >= 7
        assert "construction" in profile.industries


class TestScoreResumeMatch:
    """score_resume_match returns 0..1 capturing resume↔job fit."""

    def test_empty_profile_returns_neutral(self) -> None:
        profile = ResumeProfile()
        score, _matched = score_resume_match(_job(), profile)
        # Empty profile gets a neutral score (no signal, no penalty)
        assert 0.20 <= score <= 0.45

    def test_nurse_resume_matches_nursing_job(self) -> None:
        profile = build_resume_profile(
            "Registered nurse, 10 years ICU experience. BLS, ACLS."
        )
        nursing_job = _job(
            title="Patient Care Technician",
            company="JPS Health Network",
            description=(
                "Provide direct nursing assistance to patients. "
                "Take vitals, assist nurses, hospital ward."
            ),
        )
        warehouse_job = _job(
            title="Warehouse Associate",
            company="Hillwood",
            description="Pick, pack, ship at the AllianceTexas warehouse. Forklift cert provided.",
        )
        score_nurse, _ = score_resume_match(nursing_job, profile)
        score_warehouse, _ = score_resume_match(warehouse_job, profile)
        assert score_nurse > score_warehouse
        assert score_nurse >= 0.5

    def test_forklift_resume_matches_warehouse_job(self) -> None:
        profile = build_resume_profile(
            "Forklift operator, 5 years warehouse experience. OSHA-10."
        )
        warehouse_job = _job(
            title="Warehouse Associate",
            company="Hillwood",
            description="Pick, pack, ship at the AllianceTexas warehouse. Forklift cert provided.",
        )
        nursing_job = _job(
            title="Patient Care Technician",
            company="JPS Health Network",
            description="Provide nursing assistance. Hospital ward.",
        )
        score_warehouse, _ = score_resume_match(warehouse_job, profile)
        score_nursing, _ = score_resume_match(nursing_job, profile)
        assert score_warehouse > score_nursing
        assert score_warehouse >= 0.5

    def test_match_returns_specific_signals(self) -> None:
        """match list should name actual matched signals, not generic."""
        profile = build_resume_profile(
            "Registered nurse, 10 years ICU experience. BLS certified."
        )
        nursing_job = _job(
            title="Patient Care Tech",
            company="JPS",
            description="Nursing assistance, hospital, BLS preferred.",
        )
        _, matched = score_resume_match(nursing_job, profile)
        # At least one matched signal should mention nurse/healthcare/BLS
        joined = " ".join(matched).lower()
        assert any(kw in joined for kw in ("nurse", "nursing", "health", "bls"))
