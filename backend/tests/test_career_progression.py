"""Tests for career progression hints (Pattern 12)."""

from __future__ import annotations

from app.modules.matching.career_progression import (
    detect_progression,
    detect_progression_for_matches,
)


_CNA_RN_JOB = {
    "title": "Registered Nurse - Tuition Reimbursement",
    "company": "Texas Health Resources",
    "description": (
        "We're hiring RNs and offer full tuition reimbursement for CNAs "
        "looking to advance into RN roles. Sponsorship available."
    ),
}

_RN_ONLY_JOB = {
    "title": "Registered Nurse",
    "company": "Texas Health Resources",
    "description": "Must hold an active Texas RN license.",
}

_FORKLIFT_LEAD_JOB = {
    "title": "Warehouse Supervisor",
    "company": "Amazon",
    "description": (
        "Looking for warehouse supervisors. We promote from within and "
        "offer leadership training for our forklift operators."
    ),
}

_CASHIER_JOB = {
    "title": "Cashier",
    "company": "HEB",
    "description": "Front-end cashier position. Must be 18+.",
}


class TestDetectProgression:
    def test_cna_to_rn_with_training_returns_hint(self) -> None:
        hint = detect_progression(["cna"], _CNA_RN_JOB)
        assert hint is not None
        assert hint.junior_role == "CNA"
        assert hint.senior_role == "RN"
        assert "training pathway" in hint.text

    def test_cna_to_rn_no_training_returns_none(self) -> None:
        """RN-only ad without training language -> no hint."""
        hint = detect_progression(["cna"], _RN_ONLY_JOB)
        assert hint is None

    def test_warehouse_to_supervisor_with_path_returns_hint(self) -> None:
        hint = detect_progression(["warehouse"], _FORKLIFT_LEAD_JOB)
        assert hint is not None
        assert hint.senior_role == "warehouse supervisor"

    def test_unrelated_job_returns_none(self) -> None:
        hint = detect_progression(["cna"], _CASHIER_JOB)
        assert hint is None

    def test_empty_families_returns_none(self) -> None:
        hint = detect_progression([], _CNA_RN_JOB)
        assert hint is None

    def test_unknown_family_returns_none(self) -> None:
        hint = detect_progression(["unknown_family"], _CNA_RN_JOB)
        assert hint is None


class TestDetectProgressionForMatches:
    def test_returns_index_keyed_dict(self) -> None:
        matches = [_CASHIER_JOB, _CNA_RN_JOB, _RN_ONLY_JOB]
        hints = detect_progression_for_matches(["cna"], matches)
        assert 0 not in hints       # cashier — no progression
        assert 1 in hints           # CNA->RN match
        assert 2 not in hints       # RN-only — no training
        assert hints[1].senior_role == "RN"

    def test_pydantic_model_shape_supported(self) -> None:
        """Match-like objects with title/company/match_reason attrs work."""
        class _M:
            title = "Registered Nurse - tuition reimbursement"
            company = "TX Health"
            match_reason = "RN-to-be sponsorship for CNAs"
        hints = detect_progression_for_matches(["cna"], [_M()])
        assert 0 in hints
