"""Tests for jobs funnel analytics (T12.12).

Covers:
- compute_funnel: per-session counts + conversion rates
- compute_community_funnel: city-scoped aggregates with k-anonymity
- Segmentation: cleared_barriers, fair_chance_employer, industry
- Demo session guard (documented if column absent)
- intelligence.py additive integration
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.core.migrations import runner
from app.modules.common.temporal_types import JobApplicationStatus
from app.modules.jobs import applications, funnel_analytics
from app.modules.jobs.funnel_analytics import (
    MIN_K_ANONYMITY,
    FunnelCounts,
    FunnelResult,
    SuppressedCell,
    compute_community_funnel,
    compute_funnel,
)

_CITY = "montgomery"
_OTHER_CITY = "fort-worth"


# -------------------- Fixtures + seed helpers --------------------


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "funnel.db")
    runner.apply_pending(path)
    return path


def _seed_session(
    path: str,
    session_id: str,
    *,
    profile: dict | None = None,
    city: str | None = _CITY,
) -> None:
    """Insert a session row and (optionally) an outcomes_records row tagging city."""
    conn = sqlite3.connect(path)
    try:
        now = datetime.now(timezone.utc).isoformat()
        profile_json = json.dumps(profile) if profile is not None else None
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, profile, expires_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_id, now, "[]", profile_json, now),
        )
        if city is not None:
            conn.execute(
                "INSERT INTO outcomes_records "
                "(session_id, event_type, payload_json, created_at, "
                "barriers_cleared_snapshot_json) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    session_id,
                    "session_tagged",
                    json.dumps({"city": city}),
                    now,
                    "[]",
                ),
            )
        conn.commit()
    finally:
        conn.close()


def _make_app(
    session_id: str,
    *,
    db_path: str,
    status: JobApplicationStatus = JobApplicationStatus.DRAFT,
    company: str = "Acme",
    match_url_suffix: str = "",
):
    app = applications.create(
        session_id,
        match_source="indeed",
        match_url=f"https://indeed.com/job/{session_id}{match_url_suffix}",
        company=company,
        role="Tech",
        db_path=db_path,
    )
    if status is not JobApplicationStatus.DRAFT:
        # Walk through the transition chain to reach target status.
        chain = _transition_chain(status)
        current = JobApplicationStatus.DRAFT
        for nxt in chain:
            applications.update_status(app.id, nxt, db_path=db_path)
            current = nxt
        _ = current
    return app


def _transition_chain(target: JobApplicationStatus) -> list[JobApplicationStatus]:
    """Minimal legal chain DRAFT -> target via ALLOWED matrix."""
    chains: dict[JobApplicationStatus, list[JobApplicationStatus]] = {
        JobApplicationStatus.APPLIED: [JobApplicationStatus.APPLIED],
        JobApplicationStatus.INTERVIEW: [
            JobApplicationStatus.APPLIED, JobApplicationStatus.INTERVIEW,
        ],
        JobApplicationStatus.OFFER: [
            JobApplicationStatus.APPLIED,
            JobApplicationStatus.INTERVIEW,
            JobApplicationStatus.OFFER,
        ],
        JobApplicationStatus.REJECTED: [
            JobApplicationStatus.APPLIED, JobApplicationStatus.REJECTED,
        ],
        JobApplicationStatus.WITHDRAWN: [
            JobApplicationStatus.APPLIED, JobApplicationStatus.WITHDRAWN,
        ],
    }
    return chains[target]


def _seed_cohort(
    db_path: str,
    n: int,
    *,
    prefix: str,
    city: str = _CITY,
    status: JobApplicationStatus = JobApplicationStatus.APPLIED,
    profile: dict | None = None,
) -> list[str]:
    """Create n sessions each with one application at `status`. Returns session IDs."""
    ids: list[str] = []
    for i in range(n):
        sid = f"{prefix}-{i:08d}-bbbb-cccc-dddd-eeeeeeeeeeee"
        _seed_session(db_path, sid, profile=profile, city=city)
        _make_app(sid, db_path=db_path, status=status)
        ids.append(sid)
    return ids


# -------------------- compute_funnel (per-session) --------------------


def test_compute_funnel_empty_session(db_path: str) -> None:
    _seed_session(db_path, "empty-sid-aaaa-bbbb-cccc-dddddddddddd")
    result = compute_funnel(
        "empty-sid-aaaa-bbbb-cccc-dddddddddddd", db_path=db_path,
    )
    assert isinstance(result, FunnelResult)
    assert result.counts == FunnelCounts(
        draft=0, applied=0, interview=0, offer=0, rejected=0, withdrawn=0,
    )
    assert result.draft_to_applied_rate is None
    assert result.applied_to_interview_rate is None
    assert result.interview_to_offer_rate is None


def test_compute_funnel_single_session_counts(db_path: str) -> None:
    sid = "11111111-bbbb-cccc-dddd-eeeeeeeeeeee"
    _seed_session(db_path, sid)
    _make_app(sid, db_path=db_path, status=JobApplicationStatus.DRAFT)
    _make_app(
        sid, db_path=db_path, status=JobApplicationStatus.APPLIED,
        match_url_suffix="-a",
    )
    _make_app(
        sid, db_path=db_path, status=JobApplicationStatus.INTERVIEW,
        match_url_suffix="-b",
    )
    _make_app(
        sid, db_path=db_path, status=JobApplicationStatus.OFFER,
        match_url_suffix="-c",
    )

    result = compute_funnel(sid, db_path=db_path)
    # Each application is in exactly one status (current).
    assert result.counts.draft == 1
    assert result.counts.applied == 1
    assert result.counts.interview == 1
    assert result.counts.offer == 1
    # Rates: applied have funnelled down — include current + later stages in numerator.
    # draft_to_applied = (applied+interview+offer+rejected+withdrawn) / (all)
    # = 3 / 4 = 0.75
    assert result.draft_to_applied_rate == pytest.approx(0.75)
    # applied_to_interview = (interview+offer) / (applied+interview+offer+rejected+withdrawn)
    # = 2 / 3 (rounded to 4dp in implementation)
    assert result.applied_to_interview_rate == pytest.approx(2 / 3, abs=1e-3)
    # interview_to_offer = offer / (interview+offer)  = 1/2
    assert result.interview_to_offer_rate == pytest.approx(0.5)


def test_conversion_rates_handle_zero_denominator(db_path: str) -> None:
    """A session with only DRAFT apps: applied/interview/offer rates are None."""
    sid = "22222222-bbbb-cccc-dddd-eeeeeeeeeeee"
    _seed_session(db_path, sid)
    _make_app(sid, db_path=db_path, status=JobApplicationStatus.DRAFT)

    result = compute_funnel(sid, db_path=db_path)
    assert result.counts.draft == 1
    # draft_to_applied denominator is all (1) but numerator is 0 → 0.0 (valid rate)
    assert result.draft_to_applied_rate == 0.0
    # applied_to_interview denominator is 0 → None
    assert result.applied_to_interview_rate is None
    assert result.interview_to_offer_rate is None


# -------------------- compute_community_funnel: k-anonymity --------------------


def test_community_funnel_empty_db(db_path: str) -> None:
    """Empty DB: no PII risk → return zero counts under '__all__' key, not suppressed."""
    result = compute_community_funnel(_CITY, db_path=db_path)
    assert "__all__" in result
    cell = result["__all__"]
    assert isinstance(cell, FunnelResult)
    assert cell.counts.draft == 0
    assert cell.counts.applied == 0


def test_community_funnel_single_session_suppresses(db_path: str) -> None:
    _seed_cohort(db_path, 1, prefix="single")
    result = compute_community_funnel(_CITY, db_path=db_path)
    cell = result["__all__"]
    assert isinstance(cell, SuppressedCell)
    assert cell.count is None
    assert cell.suppressed is True
    assert cell.reason == "k_anonymity_min_5"


def test_community_funnel_4_sessions_suppresses(db_path: str) -> None:
    _seed_cohort(db_path, 4, prefix="four")
    result = compute_community_funnel(_CITY, db_path=db_path)
    assert isinstance(result["__all__"], SuppressedCell)


def test_community_funnel_5_sessions_returns_counts(db_path: str) -> None:
    _seed_cohort(db_path, MIN_K_ANONYMITY, prefix="five")
    result = compute_community_funnel(_CITY, db_path=db_path)
    cell = result["__all__"]
    assert isinstance(cell, FunnelResult)
    assert cell.counts.applied == 5


# -------------------- Segmentation: cleared_barriers --------------------


def test_community_funnel_by_cleared_barriers(db_path: str) -> None:
    # 6 sessions with dmv cleared (exceeds k=5), 4 without (suppressed)
    _seed_cohort(
        db_path, 6, prefix="dmvA",
        profile={"cleared_barriers": ["dmv"]},
    )
    _seed_cohort(
        db_path, 4, prefix="nodmvB",
        profile={"cleared_barriers": []},
    )
    result = compute_community_funnel(
        _CITY, segment_by="cleared_barriers", db_path=db_path,
    )
    # "dmv" group has 6 sessions → FunnelResult
    assert "dmv" in result
    assert isinstance(result["dmv"], FunnelResult)
    assert result["dmv"].counts.applied == 6
    # "__none__" group has 4 sessions → suppressed
    assert "__none__" in result
    assert isinstance(result["__none__"], SuppressedCell)


# -------------------- Segmentation: fair_chance_employer --------------------


def test_community_funnel_by_fair_chance_employer(db_path: str) -> None:
    """6 sessions apply to fair-chance 'FairCo'; 4 apply to regular 'RegCo'."""

    def fake_lookup(company: str, city: str) -> bool:
        return company == "FairCo"

    for i in range(6):
        sid = f"fairA-{i:08d}-bbbb-cccc-dddd-eeeeeeeeeeee"
        _seed_session(db_path, sid)
        _make_app(
            sid, db_path=db_path, status=JobApplicationStatus.APPLIED,
            company="FairCo",
        )
    for i in range(4):
        sid = f"regB-{i:08d}-bbbb-cccc-dddd-eeeeeeeeeeee"
        _seed_session(db_path, sid)
        _make_app(
            sid, db_path=db_path, status=JobApplicationStatus.APPLIED,
            company="RegCo",
        )

    result = compute_community_funnel(
        _CITY,
        segment_by="fair_chance_employer",
        db_path=db_path,
        fair_chance_lookup=fake_lookup,
    )
    assert isinstance(result["true"], FunnelResult)
    assert result["true"].counts.applied == 6
    assert isinstance(result["false"], SuppressedCell)


# -------------------- City scope isolation --------------------


def test_community_funnel_city_scope_isolation(db_path: str) -> None:
    _seed_cohort(db_path, 6, prefix="mont", city=_CITY)
    _seed_cohort(db_path, 5, prefix="ftw", city=_OTHER_CITY)
    mont = compute_community_funnel(_CITY, db_path=db_path)
    ftw = compute_community_funnel(_OTHER_CITY, db_path=db_path)

    mont_cell = mont["__all__"]
    ftw_cell = ftw["__all__"]
    assert isinstance(mont_cell, FunnelResult)
    assert isinstance(ftw_cell, FunnelResult)
    assert mont_cell.counts.applied == 6
    assert ftw_cell.counts.applied == 5


# -------------------- Demo session guard --------------------


def test_community_funnel_excludes_demo_sessions(db_path: str) -> None:
    """Demo guard: sessions.demo column lands in S12b T12.34.

    Our guard: skip if column absent (safe fallback). When column exists,
    `demo=1` rows are excluded from aggregates.
    """
    conn = sqlite3.connect(db_path)
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(sessions)").fetchall()}
    finally:
        conn.close()
    if "demo" not in cols:
        pytest.skip("demo column lands in S12b T12.34 — guard tested when column exists")

    # Seed 6 real + 3 demo
    real_ids = _seed_cohort(db_path, 6, prefix="real")
    _ = real_ids
    # Flag 3 extras as demo
    conn = sqlite3.connect(db_path)
    try:
        for i in range(3):
            sid = f"demo-{i:08d}-bbbb-cccc-dddd-eeeeeeeeeeee"
            conn.execute(
                "INSERT INTO sessions (id, created_at, barriers, expires_at, demo) "
                "VALUES (?, ?, '[]', ?, 1)",
                (sid, "2026-01-01T00:00:00", "2027-01-01T00:00:00"),
            )
        conn.commit()
    finally:
        conn.close()
    for i in range(3):
        sid = f"demo-{i:08d}-bbbb-cccc-dddd-eeeeeeeeeeee"
        _make_app(sid, db_path=db_path, status=JobApplicationStatus.APPLIED)

    result = compute_community_funnel(_CITY, db_path=db_path)
    cell = result["__all__"]
    assert isinstance(cell, FunnelResult)
    assert cell.counts.applied == 6  # demo excluded


# -------------------- Industry segmentation (unsupported) --------------------


def test_industry_segment_returns_unsupported(db_path: str) -> None:
    _seed_cohort(db_path, 6, prefix="ind")
    result = compute_community_funnel(
        _CITY, segment_by="industry", db_path=db_path,
    )
    # Documented TODO: job_applications has no industry column
    assert "__unsupported__" in result
    assert isinstance(result["__unsupported__"], SuppressedCell)


# -------------------- intelligence.py integration --------------------


def test_build_application_conversion_rates_shape(db_path: str) -> None:
    """Pure helper returns the three-key shape regardless of DB state."""
    out = funnel_analytics.build_application_conversion_rates(
        _CITY, db_path=db_path,
    )
    assert set(out.keys()) == {"city_scoped", "by_cleared_barriers", "by_fair_chance"}
    # Empty DB: city_scoped shows zero counts under __all__ (no PII risk)
    assert "__all__" in out["city_scoped"]


@pytest.mark.anyio
async def test_intelligence_endpoint_adds_application_conversion_rates(
    client,
) -> None:
    """GET /api/intelligence/barriers includes application_conversion_rates."""
    resp = await client.get("/api/intelligence/barriers")
    assert resp.status_code == 200
    data = resp.json()
    assert "application_conversion_rates" in data
    acr = data["application_conversion_rates"]
    assert set(acr.keys()) == {
        "city_scoped", "by_cleared_barriers", "by_fair_chance",
    }


@pytest.mark.anyio
async def test_intelligence_endpoint_existing_fields_unchanged(client) -> None:
    """Additive guard: the canonical pre-T12.12 response keys still present."""
    resp = await client.get("/api/intelligence/barriers")
    data = resp.json()
    # From test_intelligence_route.py baseline — must still be present.
    for key in (
        "barriers", "confidence", "calibrated_weeks",
        "default_weeks", "total_feedback_count", "avg_plan_accuracy",
    ):
        assert key in data, f"regression: {key!r} missing after T12.12"
