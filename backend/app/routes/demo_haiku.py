"""Demo walkthrough + health endpoints (Agent-2 demo polish).

- GET /api/demo/walkthrough?persona=carlos
  Returns one canned, deterministic end-to-end demo flow.
- GET /api/demo/personas
  List the available persona ids.
- GET /health/demo
  Freshness state of every data source + LLM connectivity in one curl.

These endpoints are PUBLIC (no auth) — intended for hackathon judges
to evaluate quickly.  No PII, no DB writes.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request

from app.demo.persona_loader import (
    PersonaNotFound,
    get_persona,
    list_persona_ids,
)
from app.demo.walkthrough import build_walkthrough

router = APIRouter(prefix="/api/demo", tags=["demo_haiku"])
health_router = APIRouter(prefix="/health", tags=["health"])

_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


@router.get("/personas")
def list_demo_personas() -> dict:
    """List demo persona ids and their summaries."""
    out: dict[str, dict] = {}
    for pid in list_persona_ids():
        try:
            p = get_persona(pid)
        except PersonaNotFound:
            continue
        out[pid] = {
            "display_name": p["display_name"],
            "summary": p["summary"],
            "primary_barriers": p["primary_barriers"],
        }
    return {"personas": out, "count": len(out)}


@router.get("/walkthrough")
def demo_walkthrough(
    persona: str = Query(default="carlos", min_length=2, max_length=40),
) -> dict:
    """Return a canned, deterministic end-to-end demo for one persona."""
    try:
        return build_walkthrough(persona)
    except PersonaNotFound:
        raise HTTPException(
            status_code=404, detail=f"Persona '{persona}' not found",
        )


def _file_age_days(path: Path) -> float | None:
    """Return age in days for a file; None if it doesn't exist."""
    if not path.exists():
        return None
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    delta = datetime.now(tz=timezone.utc) - mtime
    return round(delta.total_seconds() / 86400.0, 1)


def _data_source_status() -> dict:
    """Surface the freshness of each known data source."""
    return {
        "fw_jobs_listings": {
            "path": "data/cities/fort-worth/honestjobs_listings.json",
            "age_days": _file_age_days(
                _DATA_DIR / "cities" / "fort-worth" / "honestjobs_listings.json",
            ),
        },
        "fw_resources": {
            "path": "data/cities/fort-worth/resources.json",
            "age_days": _file_age_days(
                _DATA_DIR / "cities" / "fort-worth" / "resources.json",
            ),
        },
        "rag_index": {
            "path": "data/rag_index/index.faiss",
            "age_days": _file_age_days(
                _DATA_DIR / "rag_index" / "index.faiss",
            ),
        },
    }


def _llm_status() -> dict:
    """Surface LLM connectivity (key presence; not a live call)."""
    has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
    return {
        "anthropic_key_present": has_anthropic,
        "model": os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001"),
    }


def _persona_status() -> dict:
    return {
        "registered": list_persona_ids(),
        "count": len(list_persona_ids()),
    }


@health_router.get("/demo")
def health_demo(request: Request) -> dict:
    """One-curl freshness check — data sources + LLM + RAG + personas.

    Always returns 200; never throws.  ``status: green`` only when every
    expected component is present and fresh (<14 days for data files).
    """
    data_sources = _data_source_status()
    llm = _llm_status()
    personas = _persona_status()
    rag_ready = False
    store = getattr(request.app.state, "rag_store", None)
    if store is not None and getattr(store, "is_ready", lambda: False)():
        rag_ready = True

    issues: list[str] = []
    for name, info in data_sources.items():
        age = info.get("age_days")
        if age is None:
            issues.append(f"{name}: missing")
        elif age > 14:
            issues.append(f"{name}: stale ({age}d)")
    if not llm["anthropic_key_present"]:
        issues.append("anthropic_key: missing")
    if not rag_ready:
        issues.append("rag_index: not loaded")
    if personas["count"] < 5:
        issues.append("personas: incomplete")

    return {
        "status": "green" if not issues else "yellow",
        "issues": issues,
        "data_sources": data_sources,
        "llm": llm,
        "rag_index_loaded": rag_ready,
        "personas": personas,
        "checked_at": datetime.now(tz=timezone.utc).isoformat(),
    }
