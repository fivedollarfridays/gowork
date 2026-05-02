"""Industry-coherence tests for the relevance scorer.

These tests pin Stage-2 fixes:

1. Title-family detection uses word boundaries — "rn " inside
   "lea**rn** carpentry" must NOT be flagged as a nursing job.
2. Wrong-industry jobs are penalised so a 10-yr nurse never ties
   with a construction listing in the top scores.
3. Experience-years credit is conditional on industry alignment —
   10 yrs of nursing does not earn full "years" credit on a
   construction job.
"""

from __future__ import annotations

from app.modules.matching.relevance_factors import job_families, job_industries
from app.modules.matching.relevance_scorer import (
    build_resume_profile,
    score_resume_match,
)


def _construction_apprentice() -> dict:
    """JE Dunn Construction Apprentice — the regression sentinel."""
    return {
        "title": "Construction Apprentice",
        "company": "JE Dunn Construction",
        "location": "Fort Worth, TX 76102",
        "description": (
            "Entry-level apprenticeship on commercial build sites across DFW. "
            "Learn carpentry, concrete, and site safety. OSHA-10 within 30 "
            "days. Tools provided. Pay: $19.00/hr. Reentry-friendly employer. "
            "Construction labor."
        ),
    }


def _registered_nurse_job() -> dict:
    return {
        "title": "Registered Nurse - Med Surg",
        "company": "JPS Health Network",
        "location": "Fort Worth, TX 76104",
        "description": (
            "Registered Nurse RN role on med-surg unit. BSN preferred. "
            "BLS ACLS required. 12 hour shifts. Pay: $34.00/hr."
        ),
    }


def _nurse_resume_text() -> str:
    return (
        "Registered Nurse RN with 10 years critical care ICU experience. "
        "BLS ACLS PALS certifications. Skilled in IV insertion patient "
        "assessment electronic health records EHR Epic. BSN Bachelor of "
        "Science in Nursing."
    )


class TestTitleFamilyWordBoundary:
    """job_families must NOT match title fragments inside other words."""

    def test_construction_job_is_not_tagged_nursing(self) -> None:
        """The 'rn ' in 'leaRN carpentry' must not promote to nursing."""
        fams = job_families(_construction_apprentice())
        assert "nursing" not in fams, (
            f"Construction Apprentice falsely tagged as nursing: {fams}"
        )

    def test_construction_job_keeps_construction_family(self) -> None:
        """The legit construction signal must still surface."""
        fams = job_families(_construction_apprentice())
        assert "general_construction" in fams

    def test_real_nurse_job_still_tagged_nursing(self) -> None:
        """Real nurse listings should still resolve to the nursing family."""
        fams = job_families(_registered_nurse_job())
        assert "nursing" in fams


class TestIndustryMismatchPenalty:
    """A 10-yr nurse must score the construction listing < the RN listing."""

    def test_nurse_resume_construction_score_capped(self) -> None:
        """Nurse vs construction listing must land < 0.45 after Stage 2."""
        profile = build_resume_profile(_nurse_resume_text())
        score, _ = score_resume_match(_construction_apprentice(), profile)
        # Pre-fix: 0.40. Post-fix: industry mismatch + word-boundary +
        # conditional experience must push this clearly below 0.40.
        assert score < 0.35, f"Construction score for nurse stayed at {score}"

    def test_nurse_resume_construction_below_real_nurse_job(self) -> None:
        """And the construction score must trail the real RN job by a wide gap."""
        profile = build_resume_profile(_nurse_resume_text())
        construction_score, _ = score_resume_match(_construction_apprentice(), profile)
        nurse_score, _ = score_resume_match(_registered_nurse_job(), profile)
        assert nurse_score - construction_score >= 0.40, (
            f"Gap too small: nurse={nurse_score} construction={construction_score}"
        )


class TestExperienceConditionalOnIndustry:
    """factor_years should not award 1.0 when the industries don't align."""

    def test_construction_job_not_awarded_full_nurse_years(self) -> None:
        """A 10-yr nurse on a construction listing -> zero years signal."""
        profile = build_resume_profile(_nurse_resume_text())
        _, signals = score_resume_match(_construction_apprentice(), profile)
        joined = " ".join(signals).lower()
        assert "10 yrs" not in joined and "yrs experience" not in joined, (
            f"Years credit leaked across industries: {signals}"
        )


class TestJobIndustryInference:
    """job_industries must reflect the actual industry, not collateral hits."""

    def test_construction_apprentice_industry_is_construction(self) -> None:
        """Construction-tagged listings should expose construction in industries."""
        inds = job_industries(_construction_apprentice())
        assert "construction" in inds

    def test_construction_apprentice_not_tagged_healthcare(self) -> None:
        """And must NOT be falsely tagged healthcare from cross-keyword leakage."""
        inds = job_industries(_construction_apprentice())
        assert "healthcare" not in inds
