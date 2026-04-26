"""S13 T13.3 — QC Reset CLI.

Wipe every demo-flagged row across the worker-companion schema and
(optionally) reseed via the T13.2 demo factory. Designed to keep QC
suites honest: each suite can call this between runs to land on a
deterministic, freshly seeded baseline in under 5 seconds.

Wipe scope (delegated to :mod:`_qc_reset_wipe`)
-----------------------------------------------
1. Direct ``demo=1`` rows in ``sessions`` (preserving the ``_advisor_audit``
   placeholder, which is recreated on demand by the advisor inbox routes
   but that other code paths assume is always present).
2. Cascade-via-``session_id``: every child table whose rows reference a
   demo session via ``session_id``. We delete these BEFORE wiping the
   sessions row so audit / debug queries can correlate the cleanup.
3. Hashed-session-id rows in ``compliance_audit`` (keyed by
   ``sha256(session_id)``) for the demo session ids.
4. Demo-specific rows in shared tables: ``advisor_tokens`` rows planted
   by the seed (``advisor_id LIKE 'adv-demo-%'``) and ``sendgrid_events``
   rows whose deterministic ``message_id`` is ``demo-sendgrid-msg-...``.

Non-demo data is never touched — every DELETE is scoped by either
``demo = 1`` (excluding the placeholder), the demo session-id list, or
a deterministic ``demo-`` prefix on the row.

Usage
-----
``python scripts/qc_reset.py [--db-path PATH] [--no-reseed]``

Default ``db_path`` is resolved from ``backend/app.core.config`` via the
``database_url`` (sqlite+aiosqlite:///path) form, matching how the rest
of the codebase locates the dev DB. Speed budget is 5 seconds; the
wipe runs in a single transaction so partial state never persists.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---- sys.path bootstrap so this script imports from `backend/app/`. ----
# The script lives at <repo>/scripts/, but the application code is under
# <repo>/backend/app/. Adding backend/ makes ``import app.demo_seed`` work
# when launched from anywhere (CI, dev shell, pytest subprocess).
_REPO_ROOT = Path(__file__).resolve().parent.parent
_BACKEND_DIR = _REPO_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# Bootstrap the scripts/ directory itself so the wipe-helpers spoke is
# importable regardless of cwd at invocation time.
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from app.demo_seed import seed_worker_companion_sessions  # noqa: E402
from _qc_reset_wipe import (  # noqa: E402
    PLACEHOLDER_SESSION_ID,
    wipe_demo_rows,
)


def main(
    db_path: str,
    *,
    reseed: bool = True,
    now: datetime | None = None,
) -> dict:
    """Wipe demo rows and (optionally) reseed via the T13.2 factory.

    Returns a summary dict::

        {
            "deleted": {"sessions": 10, "appointments": 10, ...},
            "reseeded": True,
            "sessions_after_reseed": 10,
        }

    Idempotent: running twice on a clean DB yields the same end state.
    """
    now = now or datetime.now(timezone.utc)
    deleted = wipe_demo_rows(db_path)
    sessions_after = 0
    if reseed:
        seed_worker_companion_sessions(db_path=db_path, now=now)
        sessions_after = _count_demo_sessions(db_path)
    return {
        "deleted": deleted,
        "reseeded": reseed,
        "sessions_after_reseed": sessions_after,
    }


def _count_demo_sessions(db_path: str) -> int:
    import sqlite3

    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE demo = 1 AND id != ?",
            (PLACEHOLDER_SESSION_ID,),
        ).fetchone()
    finally:
        conn.close()
    return int(row[0]) if row else 0


def _resolve_default_db_path() -> str:
    """Pull the default sqlite path from ``app.core.config.Settings``.

    Mirrors how ``app.integrations.email.core.resolve_db_path`` parses
    the ``database_url``. Falls back to ``./montgowork.db`` if config is
    unavailable (fresh checkout / missing .env).
    """
    try:
        from app.core.config import get_settings
        db_url = get_settings().database_url
    except Exception:
        return "./montgowork.db"
    marker = ":///"
    idx = db_url.find(marker)
    if idx == -1:
        return "./montgowork.db"
    raw = db_url[idx + len(marker):]
    return raw or "./montgowork.db"


def _format_summary(summary: dict) -> str:
    """Render the summary as a human-readable block."""
    deleted = summary["deleted"]
    lines = ["QC reset complete.", "", "Rows deleted:"]
    for table, count in sorted(deleted.items(), key=lambda kv: kv[0]):
        lines.append(f"  {table:>28s}: {count}")
    lines.append("")
    if summary["reseeded"]:
        lines.append(f"Reseeded: {summary['sessions_after_reseed']} demo sessions")
    else:
        lines.append("Reseeded: NO (--no-reseed)")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qc_reset",
        description=(
            "Wipe demo-flagged rows across the worker-companion schema "
            "and reseed via the T13.2 demo factory."
        ),
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="Path to the sqlite DB. Defaults to settings.database_url.",
    )
    parser.add_argument(
        "--no-reseed",
        dest="reseed",
        action="store_false",
        help="Skip the reseed step (wipe only).",
    )
    parser.set_defaults(reseed=True)
    return parser


def cli(argv: list[str] | None = None) -> int:
    """Argparse entry point. Returns process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    db_path = args.db_path or _resolve_default_db_path()
    db_path = os.path.expanduser(db_path)
    summary = main(db_path, reseed=args.reseed)
    print(_format_summary(summary))
    return 0


__all__ = ["main", "cli"]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(cli())
