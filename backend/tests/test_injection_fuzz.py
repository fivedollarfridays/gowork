"""Injection-filter fuzz harness — T13.57.

Locks in the S12b filter-scope expansion: for every worker-controlled
field that reaches an LLM prompt, every payload in
:data:`tests._injection_corpus.INJECTION_CORPUS` MUST short-circuit
to the deterministic template path.

Per case we assert: ``draft.generation_method == "template"``,
``injection_reason`` is set with the offending field name + matched
regex pattern (audit row), and the LLM stub is never invoked.

Running the original S12b corpus exposed 25 real bypasses — the
patterns added to :mod:`app.modules.documents.injection_filter` in
this task close those gaps. Out-of-scope bypasses (encoding tricks,
multilingual) are documented in :mod:`tests._injection_corpus`.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from app.core import feature_flags
from app.core.migrations import runner

from tests._injection_corpus import (
    INJECTION_CORPUS,
    NEGATIVE_CONTROL_CORPUS,
)

_NOW = datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc)
_TX_CITY = "fort-worth"
_DEFAULT_EMPLOYER = "BNSF Railway"

# The set of worker-controlled fields that reach an LLM prompt.
# Per the S12b expansion: profile (name/summary/notes/work_history),
# job_description (resume), job_match_ref (cover letter).
_RESUME_FIELDS: tuple[str, ...] = (
    "name",
    "summary",
    "notes",
    "work_history.title",
    "work_history.description",
    "job_description",
)
_COVER_LETTER_FIELDS: tuple[str, ...] = (
    # Profile-side fields are already covered by the resume sweep
    # above (same filter, same payloads), so we focus the cover
    # letter sweep on the job_match_ref-only inputs.
    "job_match_ref.employer",
    "job_match_ref.hiring_manager",
)

# Combined parametrize ids for clarity.
_RESUME_CASES: list[tuple[str, str, str]] = [
    (cat, payload, field)
    for cat, payload in INJECTION_CORPUS
    for field in _RESUME_FIELDS
]
_COVER_CASES: list[tuple[str, str, str]] = [
    (cat, payload, field)
    for cat, payload in INJECTION_CORPUS
    for field in _COVER_LETTER_FIELDS
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_feature_flags() -> None:
    """Force ENABLE_AI_GENERATION ON so the LLM path is the one defended.

    With the flag off, every render goes through the template path
    regardless of injection — which proves nothing about the filter.
    Flipping it on means a green test row is a real demonstration
    that the filter blocked the LLM path.
    """
    feature_flags._reset_state_for_tests()
    feature_flags._RUNTIME_OVERRIDES["ENABLE_AI_GENERATION"] = True
    yield
    feature_flags._reset_state_for_tests()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "fuzz.db")
    runner.apply_pending(path)
    return path


@pytest.fixture
def _isolate_employers_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Redirect fair_chance_index data root + clear lru_cache."""
    from app.modules.criminal import fair_chance_index

    data_root = tmp_path / "cities"
    data_root.mkdir()
    monkeypatch.setattr(fair_chance_index, "_DATA_ROOT", data_root)
    fair_chance_index.load_employers.cache_clear()
    yield data_root
    fair_chance_index.load_employers.cache_clear()


# ---------------------------------------------------------------------------
# Helpers — seed sessions + LLM sentinel
# ---------------------------------------------------------------------------


def _build_resume_profile(field: str, payload: str) -> dict[str, Any]:
    """Place ``payload`` into ``field`` for a resume-builder profile."""
    profile: dict[str, Any] = {
        "name": "Jordan Rivera",
        "first_name": "Jordan",
        "summary": "Reliable worker. Strong on teams.",
        "skills": ["forklift", "teamwork"],
        "work_history": [{
            "title": "Forklift operator",
            "employer": "Amazon warehouse",
            "dates": "2024-2025",
            "description": "Loaded pallets onto trailers.",
        }],
    }
    if field in {"name", "summary", "notes"}:
        profile[field] = payload
    elif field == "work_history.title":
        profile["work_history"][0]["title"] = payload
    elif field == "work_history.description":
        profile["work_history"][0]["description"] = payload
    elif field == "job_description":
        # injected via call kwarg, profile stays clean
        pass
    return profile


def _build_cover_profile() -> dict[str, Any]:
    return {
        "name": "Jordan Rivera",
        "first_name": "Jordan",
        "summary": "Reliable worker. Strong on teams.",
        "cleared_barriers": ["criminal_record"],
    }


def _seed_session(
    db_path: str, session_id: str, profile: dict[str, Any],
) -> None:
    now_iso = _NOW.isoformat()
    expires = (_NOW + timedelta(days=30)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO sessions (id, created_at, barriers, profile, "
            "expires_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, now_iso, json.dumps([]),
             json.dumps(profile), expires),
        )
        conn.commit()
    finally:
        conn.close()


def _seed_resume_version(db_path: str, session_id: str) -> int:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO resume_versions "
            "(session_id, doc_type, version_counter, markdown, "
            " generation_method, created_at) "
            "VALUES (?, 'resume', 1, ?, 'template', ?)",
            (session_id, "# Resume body", _NOW.isoformat()),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def _seed_employer(
    data_root: Path, employer: str, *, fair_chance: bool,
) -> None:
    city_dir = data_root / _TX_CITY
    city_dir.mkdir(exist_ok=True)
    payload = [{
        "id": 9001,
        "name": employer,
        "industry": "logistics",
        "location": "Fort Worth, TX",
        "fair_chance": fair_chance,
        "notes": "Test fixture employer.",
    }]
    (city_dir / "employers.json").write_text(json.dumps(payload))


def _llm_sentinel(monkeypatch: pytest.MonkeyPatch, module: Any) -> dict:
    """Patch ``module._call_llm`` so any invocation fails the test."""
    state = {"calls": 0}

    def _explode(*args: Any, **kwargs: Any) -> str:  # pragma: no cover
        state["calls"] += 1
        raise AssertionError(
            "LLM was invoked with worker-controlled injection payload",
        )

    monkeypatch.setattr(module, "_call_llm", _explode)
    return state


def _read_persisted_method(db_path: str, session_id: str) -> str:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT generation_method FROM resume_versions "
            "WHERE session_id = ? ORDER BY id DESC LIMIT 1",
            (session_id,),
        ).fetchone()
    finally:
        conn.close()
    assert row is not None, "no resume_versions row was written"
    return str(row[0])


# ---------------------------------------------------------------------------
# Resume fuzz — 6 fields × 52 payloads = 312 cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("category", "payload", "field"),
    _RESUME_CASES,
    ids=[f"{cat}__{field}" for cat, _, field in _RESUME_CASES],
)
def test_resume_injection_blocks_llm(
    category: str, payload: str, field: str,
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every (payload, field) → template path, LLM never invoked,
    audit trail captures the matched pattern."""
    from app.modules.documents import resume_builder

    sentinel = _llm_sentinel(monkeypatch, resume_builder)
    profile = _build_resume_profile(field, payload)
    session_id = f"sid-{category}-{field}".replace(".", "-")
    _seed_session(db_path, session_id, profile)

    jd_arg = payload if field == "job_description" else None
    draft = resume_builder.generate_resume(
        session_id, job_description=jd_arg, db_path=db_path,
    )

    assert sentinel["calls"] == 0, (
        f"LLM invoked despite injection in {field!r} (category={category})"
    )
    assert draft.generation_method == "template"
    assert _read_persisted_method(db_path, session_id) == "template"
    # Audit row: injection_reason names the field AND carries the
    # matched regex pattern. Both are required so an SOC engineer
    # reading the audit trail can attribute the block.
    assert draft.injection_reason is not None, (
        f"injection_reason missing for {category}/{field}"
    )
    assert "pattern:" in draft.injection_reason
    assert _expected_field_token(field) in draft.injection_reason


def _expected_field_token(field: str) -> str:
    """The substring we expect to find inside ``injection_reason``.

    The builder emits ``field 'name'``, ``field 'work_history[0].title'``,
    ``field 'job_description'``, etc. We assert on a stable token that
    appears in each variant.
    """
    if field.startswith("work_history."):
        return field.split(".", 1)[1]  # e.g. "title" or "description"
    return field


# ---------------------------------------------------------------------------
# Cover-letter fuzz — 2 job_match_ref fields × 52 payloads = 104 cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("category", "payload", "field"),
    _COVER_CASES,
    ids=[f"{cat}__{field}" for cat, _, field in _COVER_CASES],
)
def test_cover_letter_injection_blocks_llm(
    category: str, payload: str, field: str,
    db_path: str, monkeypatch: pytest.MonkeyPatch,
    _isolate_employers_cache: Path,
) -> None:
    """Cover-letter ``job_match_ref.*`` fields short-circuit on injection."""
    from app.modules.documents import cover_letter_builder

    sentinel = _llm_sentinel(monkeypatch, cover_letter_builder)
    session_id = f"cov-{category}-{field}".replace(".", "-")
    _seed_session(db_path, session_id, _build_cover_profile())
    rv_id = _seed_resume_version(db_path, session_id)

    if field == "job_match_ref.employer":
        employer = payload
        hiring_manager = "Pat Manager"
    else:  # job_match_ref.hiring_manager
        employer = _DEFAULT_EMPLOYER
        hiring_manager = payload

    _seed_employer(_isolate_employers_cache, employer, fair_chance=False)
    job_match = {
        "employer": employer,
        "city_slug": _TX_CITY,
        "title": "Warehouse Associate",
        "hiring_manager": hiring_manager,
    }

    draft = cover_letter_builder.generate_cover_letter(
        session_id, job_match, rv_id, db_path=db_path,
    )

    assert sentinel["calls"] == 0, (
        f"LLM invoked despite injection in {field!r} (category={category})"
    )
    assert draft.generation_method == "template"
    assert draft.injection_reason is not None
    assert "pattern:" in draft.injection_reason
    # field-name attribution: cover-letter builder uses the
    # "job_match_ref.<key>" key, so the bare key suffix is enough.
    assert field.split(".", 1)[1] in draft.injection_reason


# ---------------------------------------------------------------------------
# Negative controls — clean text routes through normally
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("category", "payload"),
    NEGATIVE_CONTROL_CORPUS,
    ids=[cat for cat, _ in NEGATIVE_CONTROL_CORPUS],
)
def test_clean_text_does_not_trigger_filter(
    category: str, payload: str,
    db_path: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Clean profile fields take the LLM path (flag is on)."""
    from app.modules.documents import resume_builder

    profile = _build_resume_profile("summary", payload)
    session_id = f"clean-{category}"
    _seed_session(db_path, session_id, profile)

    captured: list[dict] = []

    def _fake_llm(*, prompt: str, session_id: str) -> str:
        captured.append({"prompt": prompt, "session_id": session_id})
        return "# Resume\n\nClean LLM body."

    monkeypatch.setattr(resume_builder, "_call_llm", _fake_llm)

    draft = resume_builder.generate_resume(session_id, db_path=db_path)

    assert len(captured) == 1
    assert draft.generation_method == "llm"
    assert draft.injection_reason is None


# ---------------------------------------------------------------------------
# Direct filter exercise — confirms matched_pattern is populated
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("category", "payload"),
    INJECTION_CORPUS,
    ids=[cat for cat, _ in INJECTION_CORPUS],
)
def test_filter_records_matched_pattern_for_audit(
    category: str, payload: str,
) -> None:
    """``InjectionCheck.matched_pattern`` MUST be non-empty so the
    audit row written by the builders has provenance."""
    from app.modules.documents.injection_filter import check_for_injection

    result = check_for_injection({"audited_field": payload})

    assert result.clean is False, (
        f"corpus entry {category!r} bypassed the filter: {payload[:60]!r}"
    )
    assert result.offending_field == "audited_field"
    assert result.matched_pattern, "matched_pattern must be set for audit"
