"""Load demo persona profiles from backend/demo/personas/*.json.

The personas live OUTSIDE the importable ``app/`` tree (they are demo
fixtures, not source code) so we resolve the path relative to the
backend root.  Each file is a JSON dict matching the schema documented
in ``backend/demo/personas/__init__.py``.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

# backend/app/demo/persona_loader.py -> backend/demo/personas
_PERSONAS_DIR = (
    Path(__file__).resolve().parent.parent.parent / "demo" / "personas"
)

_REQUIRED_FIELDS = {
    "id", "display_name", "city", "summary", "zip_code",
    "primary_barriers", "barrier_severity",
}


class PersonaNotFound(KeyError):
    """Raised when no persona JSON matches the requested id."""


def _load_one(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    missing = _REQUIRED_FIELDS - set(data.keys())
    if missing:
        raise ValueError(
            f"{path.name} missing required fields: {sorted(missing)}",
        )
    return data


@cache
def load_all_personas() -> dict[str, dict]:
    """Return ``{persona_id: persona_dict}`` for all valid persona files.

    Cached: the personas are static; we only read them once per process.
    """
    if not _PERSONAS_DIR.is_dir():
        return {}
    out: dict[str, dict] = {}
    for path in sorted(_PERSONAS_DIR.glob("*.json")):
        try:
            data = _load_one(path)
        except (json.JSONDecodeError, ValueError):
            continue  # skip malformed
        out[data["id"]] = data
    return out


def get_persona(persona_id: str) -> dict:
    """Return one persona by id or raise PersonaNotFound."""
    personas = load_all_personas()
    if persona_id not in personas:
        raise PersonaNotFound(persona_id)
    return personas[persona_id]


def list_persona_ids() -> list[str]:
    """Return sorted list of available persona ids."""
    return sorted(load_all_personas().keys())
