"""State-machine helpers for :mod:`app.core.queries_assessments`.

Owns the transition tables (action -> status, role -> tracks), the
queue-status whitelist, and a couple of shared SQL writers. Extracted
to keep the public-API module under the per-file size limit.

Schema note: the version-status enum (T23.1) does NOT include
``request_revision``; that string is an *action* and the review sends
the version back to ``draft`` so the author can pick it up again.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


#: Track filter applied per reviewer role in :func:`list_pending_reviews`.
#: Roles not present in this map yield an empty queue.
ROLE_TRACK_FILTER: dict[str, tuple[str, ...]] = {
    "case_manager": ("vocational", "generic"),
    "dao_reviewer": ("dao_tech", "generic"),
    "sme_reviewer": ("vocational", "dao_tech", "generic"),
    "admin": ("vocational", "dao_tech", "generic"),
}

#: Versions in any of these statuses surface in the reviewer queue.
PENDING_STATUSES: tuple[str, ...] = ("draft", "in_review")

#: Mapping of reviewer action -> resulting version status.
ACTION_TO_STATUS: dict[str, str] = {
    "approve": "approved",
    "reject": "rejected",
    "request_revision": "draft",
}

#: Version statuses that block any further reviewer action.
IMMUTABLE_STATUSES: frozenset[str] = frozenset({"published", "retired"})


def utcnow_iso() -> str:
    """Return a stable UTC timestamp string for ``*_at`` columns."""
    return datetime.now(timezone.utc).isoformat()


async def load_version_status(
    session: AsyncSession, version_id: int
) -> str | None:
    """Return current ``status`` for *version_id* or None if missing."""
    result = await session.execute(
        text("SELECT status FROM assessment_versions WHERE id = :id"),
        {"id": version_id},
    )
    row = result.first()
    return row._mapping["status"] if row else None


async def insert_questions(
    session: AsyncSession, version_id: int, questions: list[dict]
) -> None:
    """Insert each question dict for *version_id* in order received."""
    for q in questions:
        await session.execute(
            text(
                "INSERT INTO assessment_questions "
                "(version_id, position, prompt, kind, "
                "rubric_json, scoring_weight) "
                "VALUES (:v, :pos, :prompt, :kind, :rubric, :weight)"
            ),
            {
                "v": version_id,
                "pos": q["position"],
                "prompt": q["prompt"],
                "kind": q["kind"],
                "rubric": q["rubric_json"],
                "weight": q.get("scoring_weight", 1.0),
            },
        )


async def insert_review_and_transition(
    session: AsyncSession,
    *,
    version_id: int,
    reviewer_id: int,
    action: str,
    comment: str | None,
) -> int:
    """Insert a review row and apply the resulting status transition.

    Caller is responsible for state-machine validation; this helper is
    purely the SQL writer + commit. Returns the new review id.
    """
    result = await session.execute(
        text(
            "INSERT INTO assessment_reviews "
            "(version_id, reviewer_id, action, comment, created_at) "
            "VALUES (:v, :r, :act, :c, :ts) RETURNING id"
        ),
        {"v": version_id, "r": reviewer_id, "act": action,
         "c": comment, "ts": utcnow_iso()},
    )
    review_id = int(result.scalar_one())
    await session.execute(
        text(
            "UPDATE assessment_versions "
            "SET status = :s, reviewed_by = :r WHERE id = :id"
        ),
        {"s": ACTION_TO_STATUS[action], "r": reviewer_id, "id": version_id},
    )
    await session.commit()
    return review_id


def build_pending_reviews_sql(
    tracks: tuple[str, ...],
) -> tuple[str, dict]:
    """Render the parameterised reviewer-queue SELECT for *tracks*.

    Returns ``(sql_string, bind_params)``. Track + status placeholders
    are generated dynamically so the IN-list is driver-agnostic on
    sqlite + postgres without resorting to vendor-specific arrays.
    """
    track_binds = {f"t{i}": t for i, t in enumerate(tracks)}
    track_placeholders = ", ".join(f":{k}" for k in track_binds)
    status_binds = {f"s{i}": s for i, s in enumerate(PENDING_STATUSES)}
    status_placeholders = ", ".join(f":{k}" for k in status_binds)
    sql = (
        "SELECT v.id AS version_id, v.assessment_id, v.version_number, "
        "v.status, v.drafted_by, v.created_at, "
        "a.slug, a.kind, a.track "
        "FROM assessment_versions v "
        "JOIN assessments a ON a.id = v.assessment_id "
        f"WHERE a.track IN ({track_placeholders}) "
        f"AND v.status IN ({status_placeholders}) "
        "ORDER BY v.created_at"
    )
    return sql, {**track_binds, **status_binds}


__all__ = [
    "ROLE_TRACK_FILTER",
    "PENDING_STATUSES",
    "ACTION_TO_STATUS",
    "IMMUTABLE_STATUSES",
    "utcnow_iso",
    "load_version_status",
    "insert_questions",
    "insert_review_and_transition",
    "build_pending_reviews_sql",
]
