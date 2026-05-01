"""Persona-level lockdown tests for the resume<->job matcher.

Stage-2 contract: each of the four Fort Worth canonical personas
must rank industry-coherent jobs in the top-3 against the live
``honestjobs_listings.json`` data.  This guards against any future
scorer change re-opening the Construction-Apprentice-in-nurse-top-10
class of bug.

Industry families (resume_industry -> set of acceptable job_industries
returned by ``relevance_factors.job_industries``) are intentionally
generous: a logistics resume can land on "transportation" *or*
"manufacturing" jobs (warehouse, freight, package handling all get
manufacturing-tagged via INDUSTRY_KEYWORDS), and that's fine.

If you add a new job to honestjobs_listings.json that doesn't get
auto-tagged with the right industry, fix the listing -- don't soften
the test.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.modules.matching.relevance_factors import job_industries
from app.modules.matching.relevance_scorer import (
    build_resume_profile,
    score_resume_match,
)

# Fort Worth listings, loaded once per session.
_FW_LISTINGS_PATH = (
    Path(__file__).parent.parent / "data" / "cities" / "fort-worth"
    / "honestjobs_listings.json"
)


# Family of acceptable industry tags per persona.  Generous on purpose:
# we care about coherence, not pedantic single-tag matches.
INDUSTRY_FAMILIES: dict[str, set[str]] = {
    "healthcare": {"healthcare"},
    "logistics": {"manufacturing", "transportation"},
    "customer_service": {"retail", "government"},
    "construction": {"construction", "manufacturing"},
}


@pytest.fixture(scope="module")
def fw_listings() -> list[dict]:
    """Fort Worth honestjobs listings, loaded once."""
    with _FW_LISTINGS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _rank(resume_text: str, listings: list[dict]) -> list[tuple[float, dict]]:
    """Score every listing against the resume; return descending order."""
    profile = build_resume_profile(resume_text)
    scored = [(score_resume_match(j, profile)[0], j) for j in listings]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def _industry_match(job: dict, family: set[str]) -> bool:
    """True if any inferred industry on the job overlaps the family."""
    inds = set(job_industries(job))
    return bool(inds & family)


# ---------- Persona 1: Nurse ----------------------------------------

NURSE_RESUME = (
    "Registered Nurse RN with 10 years critical care ICU experience. "
    "BLS ACLS PALS certifications. Skilled in IV insertion patient "
    "assessment electronic health records EHR Epic. BSN Bachelor of "
    "Science in Nursing."
)


class TestNursePersona:
    def test_top_three_are_healthcare(self, fw_listings: list[dict]) -> None:
        """All top-3 nurse matches must be healthcare-tagged."""
        ranked = _rank(NURSE_RESUME, fw_listings)
        family = INDUSTRY_FAMILIES["healthcare"]
        top3 = ranked[:3]
        for score, job in top3:
            assert _industry_match(job, family), (
                f"Non-healthcare job in nurse top-3: "
                f"{job['title']} @ {job.get('company')} (score={score})"
            )

    def test_top_match_strong(self, fw_listings: list[dict]) -> None:
        """Top match should clear 0.85 — high-confidence."""
        ranked = _rank(NURSE_RESUME, fw_listings)
        assert ranked[0][0] > 0.85

    def test_construction_not_in_top_five(self, fw_listings: list[dict]) -> None:
        """The exact regression sentinel — guard against reopening WP1."""
        ranked = _rank(NURSE_RESUME, fw_listings)
        top5_titles = [j["title"].lower() for _, j in ranked[:5]]
        assert not any("construction" in t for t in top5_titles), (
            f"Construction job leaked into top-5: {top5_titles}"
        )

    def test_score_variance_across_top_ten(
        self, fw_listings: list[dict],
    ) -> None:
        """Top-10 must span > 0.15 — no flat 0.363-style cluster."""
        ranked = _rank(NURSE_RESUME, fw_listings)
        scores = [s for s, _ in ranked[:10]]
        assert max(scores) - min(scores) > 0.15


# ---------- Persona 2: Forklift / Warehouse -------------------------

FORKLIFT_RESUME = (
    "Forklift operator certified OSHA 10. 5 years warehouse experience "
    "inventory management shipping receiving. Experience with WMS "
    "warehouse management systems. Reliable safe operator. Can lift 50 "
    "pounds."
)


class TestForkliftPersona:
    def test_top_three_are_logistics(self, fw_listings: list[dict]) -> None:
        ranked = _rank(FORKLIFT_RESUME, fw_listings)
        family = INDUSTRY_FAMILIES["logistics"]
        for score, job in ranked[:3]:
            assert _industry_match(job, family), (
                f"Non-logistics job in forklift top-3: "
                f"{job['title']} @ {job.get('company')} (score={score})"
            )

    def test_top_match_strong(self, fw_listings: list[dict]) -> None:
        ranked = _rank(FORKLIFT_RESUME, fw_listings)
        assert ranked[0][0] > 0.85

    def test_no_healthcare_in_top_five(self, fw_listings: list[dict]) -> None:
        ranked = _rank(FORKLIFT_RESUME, fw_listings)
        for score, job in ranked[:5]:
            inds = set(job_industries(job))
            assert "healthcare" not in inds, (
                f"Healthcare job leaked into forklift top-5: "
                f"{job['title']} (score={score})"
            )


# ---------- Persona 3: Office / Customer Service --------------------

CSR_RESUME = (
    "Customer service representative with 3 years experience handling "
    "inbound calls. Strong communication skills problem solving. "
    "Proficient in Microsoft Office Excel Outlook. Bilingual English "
    "Spanish. High school diploma."
)


class TestCSRPersona:
    def test_top_three_are_customer_service(
        self, fw_listings: list[dict],
    ) -> None:
        ranked = _rank(CSR_RESUME, fw_listings)
        family = INDUSTRY_FAMILIES["customer_service"]
        for score, job in ranked[:3]:
            assert _industry_match(job, family), (
                f"Non-CSR job in CSR top-3: "
                f"{job['title']} @ {job.get('company')} (score={score})"
            )

    def test_no_welding_in_top_five(self, fw_listings: list[dict]) -> None:
        ranked = _rank(CSR_RESUME, fw_listings)
        for score, job in ranked[:5]:
            title = job["title"].lower()
            assert "weld" not in title, (
                f"Welding job leaked into CSR top-5: "
                f"{job['title']} (score={score})"
            )


# ---------- Persona 4: Construction / Welding -----------------------

WELDER_RESUME = (
    "General laborer with welding certification AWS D1.1. 4 years "
    "construction experience steel framing concrete masonry. Forklift "
    "operator. OSHA 10 certified. Reliable physical condition."
)


class TestWelderPersona:
    def test_top_three_are_trades_or_manufacturing(
        self, fw_listings: list[dict],
    ) -> None:
        ranked = _rank(WELDER_RESUME, fw_listings)
        family = INDUSTRY_FAMILIES["construction"]
        for score, job in ranked[:3]:
            assert _industry_match(job, family), (
                f"Non-trades job in welder top-3: "
                f"{job['title']} @ {job.get('company')} (score={score})"
            )

    def test_no_healthcare_in_top_five(self, fw_listings: list[dict]) -> None:
        ranked = _rank(WELDER_RESUME, fw_listings)
        for score, job in ranked[:5]:
            inds = set(job_industries(job))
            assert "healthcare" not in inds, (
                f"Healthcare job leaked into welder top-5: "
                f"{job['title']} (score={score})"
            )

    def test_no_pure_retail_clerical_in_top_three(
        self, fw_listings: list[dict],
    ) -> None:
        """Welder must not see clerical/retail-only jobs in top-3."""
        ranked = _rank(WELDER_RESUME, fw_listings)
        family = INDUSTRY_FAMILIES["construction"]
        for score, job in ranked[:3]:
            inds = set(job_industries(job))
            # If the job is exclusively retail and has zero
            # construction/manufacturing tag, it's the wrong cohort.
            if "retail" in inds and not (inds & family):
                pytest.fail(
                    f"Retail-only job in welder top-3: {job['title']} "
                    f"(industries={inds}, score={score})",
                )
