"""Version persistence helpers for resume / cover-letter docs (T12.17).

Spoke off :mod:`app.modules.documents` — extracted so the routes layer
(:mod:`app.routes.documents`) and the application-create hook in
:mod:`app.routes.jobs_applications` share one source of truth for
``resume_versions`` reads + the ``use_counter`` increment, instead of
inlining sqlite into either routes or the LLM-builders.

Public surface
--------------
* :func:`get_version` — fetch a single row by id (None if missing).
* :func:`list_versions` — newest-first list scoped to ``session_id``.
* :func:`increment_use_counter` — atomic +1 for ``use_counter``.

The ``use_counter`` column lives on the m002 ``resume_versions`` table
and is incremented exactly once per ``POST /api/job-applications`` that
references the version (T12.17 hook).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

__all__ = [
    "ResumeVersion",
    "get_version",
    "increment_use_counter",
    "list_versions",
]


@dataclass(frozen=True)
class ResumeVersion:
    """One ``resume_versions`` row — read-only projection."""

    id: int
    session_id: str
    doc_type: str
    version_counter: int
    markdown: str
    generation_method: str | None
    use_counter: int
    created_at: str


_COLUMNS = (
    "id",
    "session_id",
    "doc_type",
    "version_counter",
    "markdown",
    "generation_method",
    "use_counter",
    "created_at",
)


def _row_to_version(row: Iterable) -> ResumeVersion:
    values = list(row)
    return ResumeVersion(
        id=int(values[0]),
        session_id=str(values[1]),
        doc_type=str(values[2]),
        version_counter=int(values[3]),
        markdown=str(values[4] or ""),
        generation_method=values[5],
        use_counter=int(values[6] or 0),
        created_at=str(values[7] or ""),
    )


def get_version(
    version_id: int, *, db_path: str | Path,
) -> ResumeVersion | None:
    """Return the row matching ``version_id`` or ``None`` if missing."""
    select_sql = f"SELECT {', '.join(_COLUMNS)} FROM resume_versions WHERE id = ?"
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(select_sql, (version_id,)).fetchone()
    finally:
        conn.close()
    return _row_to_version(row) if row else None


def list_versions(
    session_id: str,
    *,
    doc_type: str | None = None,
    db_path: str | Path,
) -> list[ResumeVersion]:
    """Return all versions for ``session_id``, newest ``id`` first.

    ``id`` is monotonic per insert and is a stricter ordering than
    ``created_at`` (which is a string). When ``doc_type`` is provided,
    only that flavour is returned.
    """
    cols = ", ".join(_COLUMNS)
    if doc_type is None:
        sql = (
            f"SELECT {cols} FROM resume_versions "
            "WHERE session_id = ? ORDER BY id DESC"
        )
        params: tuple = (session_id,)
    else:
        sql = (
            f"SELECT {cols} FROM resume_versions "
            "WHERE session_id = ? AND doc_type = ? ORDER BY id DESC"
        )
        params = (session_id, doc_type)
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return [_row_to_version(row) for row in rows]


def increment_use_counter(
    version_id: int, *, db_path: str | Path,
) -> int:
    """Atomically ``use_counter += 1`` for ``version_id``; return new value.

    Returns ``0`` if the row does not exist (no-op write). Routes that
    accept a worker-supplied ``resume_version_id`` should not 500 on
    a stale id — the application row already enforces FK integrity,
    so the use-counter side-effect is best-effort.
    """
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute(
            "UPDATE resume_versions SET use_counter = use_counter + 1 "
            "WHERE id = ?",
            (version_id,),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return 0
        row = conn.execute(
            "SELECT use_counter FROM resume_versions WHERE id = ?",
            (version_id,),
        ).fetchone()
    finally:
        conn.close()
    return int(row[0]) if row else 0
