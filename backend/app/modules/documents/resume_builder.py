"""Resume builder (T12.15) — LLM-gated, injection-defended.

Produces a worker resume in markdown by composing:

* :mod:`app.modules.documents.resume_keywords` — extract JD keywords
* :mod:`app.modules.documents.resume_ranking` — order work-history
* :mod:`app.modules.documents.injection_filter` — prompt-injection
  blocklist over worker free-text
* :mod:`app.modules.documents.voice` — worker-voice post-processor
* Jinja2 template ``templates/resume_base.md.j2`` (T12.14)

Two paths
---------
* **Template** — always available, deterministic, no LLM. Used when
  ``ENABLE_AI_GENERATION`` is off, when the injection filter flags
  worker text, or when the LLM raises.
* **LLM** — gated on ``ENABLE_AI_GENERATION`` AND a clean injection
  scan. On any exception from the LLM call we fall back to the
  template path so the worker still gets a resume.

Every call persists one ``resume_versions`` row with a monotonically
increasing ``version_counter`` and ``generation_method`` ∈
``{"llm", "template"}``. ``injection_reason`` is returned on the
``ResumeDraft`` (not persisted) for the caller / audit.
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
from app.modules.documents import (
    injection_filter,
    resume_keywords,
    resume_ranking,
    voice,
)
from app.modules.documents._document_status import (
    resume_nightly_status as nightly_status,
)

__all__ = ["ResumeDraft", "generate_resume", "nightly_status"]

logger = logging.getLogger(__name__)

_AI_FLAG = "ENABLE_AI_GENERATION"
_DOC_TYPE = "resume"
_TEMPLATE_NAME = "resume_base.md.j2"

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
class ResumeDraft:
    """One rendered resume draft."""

    session_id: str
    markdown: str
    generation_method: str
    version_counter: int
    injection_reason: str | None = None


# -------------------- Public API --------------------


def generate_resume(
    session_id: str,
    *,
    job_description: str | None = None,
    db_path: str | Path,
) -> ResumeDraft:
    """Build + persist one resume version for ``session_id``.

    Selection rules: template path when ``ENABLE_AI_GENERATION`` is off
    OR injection filter triggers OR the LLM call raises. LLM path only
    on clean input with the flag on and a successful LLM response.
    """
    profile = _load_profile(session_id, db_path=db_path)
    free_text = _collect_worker_free_text(profile)
    check = injection_filter.check_for_injection(free_text)
    injection_reason: str | None = None
    if not check.clean:
        injection_reason = _format_injection_reason(check)
        logger.info(
            "resume: injection detected for session=%s field=%s — template path",
            session_id, check.offending_field,
        )
    markdown, method = _render_markdown(
        session_id, profile,
        job_description=job_description,
        force_template=not check.clean,
    )
    version_counter = _persist_version(
        session_id, markdown, method, db_path=db_path,
    )
    return ResumeDraft(
        session_id=session_id,
        markdown=markdown,
        generation_method=method,
        version_counter=version_counter,
        injection_reason=injection_reason,
    )


# -------------------- Profile + field extraction --------------------


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
    """Assemble ``{field: text}`` for the injection scan.

    We scan the fields a worker can freely type into: name, summary,
    notes, and the description/title of every work-history entry. The
    scan stops at the first match so order matters — name + notes first
    because those are the likeliest attack surface.
    """
    fields: dict[str, str] = {}
    for key in ("name", "summary", "notes"):
        value = profile.get(key)
        if isinstance(value, str) and value:
            fields[key] = value
    history = profile.get("work_history")
    if isinstance(history, list):
        for idx, entry in enumerate(history):
            if not isinstance(entry, dict):
                continue
            for key in ("title", "description"):
                value = entry.get(key)
                if isinstance(value, str) and value:
                    fields[f"work_history[{idx}].{key}"] = value
    return fields


def _format_injection_reason(check: injection_filter.InjectionCheck) -> str:
    return (
        f"injection pattern in field '{check.offending_field}' "
        f"(pattern: {check.matched_pattern})"
    )


# -------------------- Render path --------------------


def _render_markdown(
    session_id: str,
    profile: dict[str, Any],
    *,
    job_description: str | None,
    force_template: bool,
) -> tuple[str, str]:
    """Pick the path (LLM or template), render, run worker-voice rules."""
    want_llm = (
        not force_template
        and feature_flags.is_enabled(_AI_FLAG, default=False)
    )
    if want_llm:
        try:
            body = _call_llm(
                prompt=_build_llm_prompt(profile, job_description),
                session_id=session_id,
            )
            return voice.apply_worker_voice(body), "llm"
        except Exception:  # noqa: BLE001 — any LLM failure → template path
            logger.exception(
                "resume: LLM failed for session=%s — falling back to template",
                session_id,
            )
    body = _render_template(profile, job_description=job_description)
    return voice.apply_worker_voice(body), "template"


def _render_template(
    profile: dict[str, Any], *, job_description: str | None,
) -> str:
    template = _JINJA_ENV.get_template(_TEMPLATE_NAME)
    context = _build_template_context(profile, job_description=job_description)
    return template.render(**context)


def _build_template_context(
    profile: dict[str, Any], *, job_description: str | None,
) -> dict[str, Any]:
    history = [
        role for role in (profile.get("work_history") or []) if isinstance(role, dict)
    ]
    if job_description:
        keywords = resume_keywords.extract_keywords(job_description)
        history = resume_ranking.rank_projects(history, keywords)
    return {
        "name": profile.get("name") or "",
        "contact": profile.get("contact") or "",
        "summary": profile.get("summary") or "",
        "skills": profile.get("skills") or [],
        "work_history": history,
        "barriers_cleared": profile.get("cleared_barriers") or [],
    }


def _build_llm_prompt(
    profile: dict[str, Any], job_description: str | None,
) -> str:
    """Compose the LLM prompt from the already-sanitised profile + JD.

    Kept as a thin string builder — ``_call_llm`` is the test seam.
    """
    bits = [
        "Write a professional worker resume in markdown.",
        "Name: " + str(profile.get("name") or ""),
        "Summary: " + str(profile.get("summary") or ""),
    ]
    if job_description:
        bits.append("Target role: " + job_description)
    return "\n\n".join(bits)


def _call_llm(*, prompt: str, session_id: str) -> str:
    """LLM entry point. Replaced in tests; the default raises.

    When ``ENABLE_AI_GENERATION`` is on in production we'll point this
    at the existing ``app.ai.llm_client`` surface; for now the flag
    defaults OFF so the production path is the template.
    """
    raise RuntimeError(
        "LLM path not wired in S12b — set ENABLE_AI_GENERATION off or "
        "monkeypatch _call_llm in tests",
    )


# -------------------- Persistence --------------------


def _persist_version(
    session_id: str, markdown: str, method: str, *, db_path: str | Path,
) -> int:
    created_at = datetime.now(timezone.utc).isoformat()
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
            " generation_method, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                session_id, _DOC_TYPE, next_counter,
                markdown, method, created_at,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return next_counter
