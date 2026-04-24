"""Cover letter builder (T12.16) — fair-chance aware.

Produces a worker cover letter in markdown, branching on the target
employer's fair-chance status. The fair-chance lookup reads from
:mod:`app.modules.criminal.fair_chance_index` (existing module, NOT
a separate JSON file) so we share the same employer corpus the rest
of the criminal-record pipeline uses.

Two branches
------------
* **Fair-chance** — addresses the criminal record using
  *employment-gap framing* drawn from the worker's barrier resolution
  timeline (``profile.cleared_barriers``). The framing names the
  cleared barrier(s) without using loaded labels — the
  :mod:`app.modules.documents.voice` post-processor strips them
  defensively if any slip through.
* **Non-fair-chance** — omits record disclosure entirely. The
  ``barriers_framed`` field on the persisted row is empty.

Two render paths (mirrors :mod:`resume_builder`)
------------------------------------------------
* **Template** — always available. Used when ``ENABLE_AI_GENERATION``
  is off, when the injection filter flags worker text, or when the
  LLM raises.
* **LLM** — gated on ``ENABLE_AI_GENERATION`` AND a clean injection
  scan. Any LLM exception falls back to the template path.

Every call persists one ``resume_versions`` row with
``doc_type='cover_letter'``, a per-(session, doc_type) monotonically
increasing ``version_counter``, and ``barriers_framed_json`` set
when (and only when) the fair-chance branch fired.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape

from app.core import feature_flags
from app.modules.criminal import fair_chance_index
from app.modules.documents import _cover_letter_branches as branches
from app.modules.documents import injection_filter, voice

__all__ = ["CoverLetterDraft", "generate_cover_letter"]

logger = logging.getLogger(__name__)

_AI_FLAG = "ENABLE_AI_GENERATION"
_DOC_TYPE = "cover_letter"
_TEMPLATE_NAME = "cover_letter_base.md.j2"

_JINJA_ENV = Environment(
    loader=PackageLoader("app.modules.documents", "templates"),
    autoescape=select_autoescape(
        enabled_extensions=("html", "xml"),
        default_for_string=False,
    ),
    keep_trailing_newline=True,
)


# -------------------- Public dataclass --------------------


@dataclass(frozen=True)
class CoverLetterDraft:
    """One rendered cover-letter draft."""

    session_id: str
    markdown: str
    generation_method: str
    version_counter: int
    fair_chance: bool
    barriers_framed: list[str]
    injection_reason: str | None = None


# -------------------- Public API --------------------


def generate_cover_letter(
    session_id: str,
    job_match_ref: dict[str, Any],
    resume_version_id: int,
    *,
    db_path: str | Path,
) -> CoverLetterDraft:
    """Build + persist one cover-letter version for ``session_id``.

    ``job_match_ref`` is an opaque dict — the keys we read are
    ``employer`` (str), ``city_slug`` (str), and optionally
    ``hiring_manager`` (str). ``resume_version_id`` is recorded by
    the caller for cross-doc lineage; we don't dereference it here.
    """
    profile = _load_profile(session_id, db_path=db_path)
    free_text = _collect_worker_free_text(profile)
    check = injection_filter.check_for_injection(free_text)
    injection_reason = _injection_reason(check)
    is_fc = _is_fair_chance(job_match_ref)
    framed = branches.barriers_to_frame(profile, is_fair_chance=is_fc)
    markdown, method = _render_markdown(
        session_id, profile, job_match_ref,
        is_fair_chance=is_fc, barriers_framed=framed,
        force_template=not check.clean,
    )
    version_counter = _persist_version(
        session_id, markdown, method, framed, db_path=db_path,
    )
    return CoverLetterDraft(
        session_id=session_id,
        markdown=markdown,
        generation_method=method,
        version_counter=version_counter,
        fair_chance=is_fc,
        barriers_framed=framed,
        injection_reason=injection_reason,
    )


# -------------------- Profile + injection scan --------------------


def _load_profile(session_id: str, *, db_path: str | Path) -> dict[str, Any]:
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT profile FROM sessions WHERE id = ?", (session_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row or not row[0]:
        return {}
    try:
        profile = json.loads(row[0])
    except (json.JSONDecodeError, TypeError):
        return {}
    return profile if isinstance(profile, dict) else {}


def _collect_worker_free_text(profile: dict[str, Any]) -> dict[str, str]:
    """Worker-supplied fields scanned for prompt injection."""
    fields: dict[str, str] = {}
    for key in ("name", "summary", "notes"):
        value = profile.get(key)
        if isinstance(value, str) and value:
            fields[key] = value
    return fields


def _injection_reason(check: injection_filter.InjectionCheck) -> str | None:
    if check.clean:
        return None
    logger.info(
        "cover_letter: injection detected field=%s — template path",
        check.offending_field,
    )
    return (
        f"injection pattern in field '{check.offending_field}' "
        f"(pattern: {check.matched_pattern})"
    )


# -------------------- Fair-chance lookup --------------------


def _is_fair_chance(job_match_ref: dict[str, Any]) -> bool:
    """Resolve fair-chance status for the target employer.

    Reads via :mod:`app.modules.criminal.fair_chance_index`. Unknown
    employers default to ``False`` (safe non-disclosure).
    """
    employer = (job_match_ref.get("employer") or "").strip()
    city_slug = (job_match_ref.get("city_slug") or "").strip()
    if not employer or not city_slug:
        return False
    for entry in fair_chance_index.get_fair_chance_employers(city_slug):
        name = entry.get("name") if isinstance(entry, dict) else None
        if isinstance(name, str) and name.strip().lower() == employer.lower():
            return True
    return False


# -------------------- Render path --------------------


def _render_markdown(
    session_id: str,
    profile: dict[str, Any],
    job_match_ref: dict[str, Any],
    *,
    is_fair_chance: bool,
    barriers_framed: list[str],
    force_template: bool,
) -> tuple[str, str]:
    """Pick the path, render, then run worker-voice rules."""
    want_llm = (
        not force_template
        and feature_flags.is_enabled(_AI_FLAG, default=False)
    )
    if want_llm:
        try:
            body = _call_llm(
                prompt=branches.build_llm_prompt(
                    profile, job_match_ref,
                    is_fair_chance=is_fair_chance,
                    barriers_framed=barriers_framed,
                ),
                session_id=session_id,
            )
            return voice.apply_worker_voice(body), "llm"
        except Exception:  # noqa: BLE001 — any LLM failure → template
            logger.exception(
                "cover_letter: LLM failed for session=%s — template fallback",
                session_id,
            )
    body = _render_template(
        profile, job_match_ref,
        is_fair_chance=is_fair_chance,
        barriers_framed=barriers_framed,
    )
    return voice.apply_worker_voice(body), "template"


def _render_template(
    profile: dict[str, Any],
    job_match_ref: dict[str, Any],
    *,
    is_fair_chance: bool,
    barriers_framed: list[str],
) -> str:
    template = _JINJA_ENV.get_template(_TEMPLATE_NAME)
    context = branches.build_template_context(
        profile, job_match_ref,
        is_fair_chance=is_fair_chance,
        barriers_framed=barriers_framed,
        date_today=datetime.now(timezone.utc).date().isoformat(),
    )
    return template.render(**context)


def _call_llm(*, prompt: str, session_id: str) -> str:
    """LLM entry point. Replaced in tests; the default raises.

    Mirrors :func:`resume_builder._call_llm` — kept as a thin seam so
    tests can monkeypatch without spinning up a real client.
    """
    raise RuntimeError(
        "LLM path not wired in S12b — set ENABLE_AI_GENERATION off or "
        "monkeypatch _call_llm in tests",
    )


# -------------------- Persistence --------------------


def _persist_version(
    session_id: str,
    markdown: str,
    method: str,
    framed: list[str],
    *,
    db_path: str | Path,
) -> int:
    created_at = datetime.now(timezone.utc).isoformat()
    framed_json = json.dumps(framed) if framed else None
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT COALESCE(MAX(version_counter), 0) FROM resume_versions "
            "WHERE session_id = ? AND doc_type = ?",
            (session_id, _DOC_TYPE),
        ).fetchone()
        next_counter = int(row[0] if row and row[0] is not None else 0) + 1
        conn.execute(
            "INSERT INTO resume_versions "
            "(session_id, doc_type, version_counter, markdown, "
            " barriers_framed_json, generation_method, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                session_id, _DOC_TYPE, next_counter,
                markdown, framed_json, method, created_at,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return next_counter
