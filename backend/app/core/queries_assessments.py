"""Async CRUD surface for the assessment authoring layer (T23.2).

Thin ``text()``-based helpers operating on an :class:`AsyncSession`,
following the :mod:`app.core.queries_accounts` pattern. ONLY callers
permitted to mutate the assessments family of tables.

State machine (enforced here; see :mod:`._assessments_state` for the
action -> status table):

* ``draft | in_review`` -> ``approved`` / ``rejected`` / back to
  ``draft`` (via record_review)
* ``approved`` -> ``published`` (publish_version)
* ``published`` -> ``retired`` (retire_version, terminal)

``published`` is otherwise IMMUTABLE — record_review on a published or
retired version raises ValueError.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core._assessments_state import (
    IMMUTABLE_STATUSES, ROLE_TRACK_FILTER, build_pending_reviews_sql,
    insert_questions, insert_review_and_transition,
    load_version_status, utcnow_iso,
)
from app.core.assessments_schema import (
    ASSESSMENT_KINDS, ASSESSMENT_TRACKS, REVIEW_ACTIONS,
)


async def create_assessment(
    session: AsyncSession,
    *,
    slug: str,
    kind: str,
    track: str,
    created_by: int,
) -> int:
    """Insert one ``assessments`` row, returning its new primary key.

    ``kind`` and ``track`` are pre-validated against the enum tuples so
    the failure mode is a clear ``ValueError`` rather than the dialect's
    opaque ``IntegrityError`` from the CHECK clause. Slug duplicates DO
    surface as ``IntegrityError`` (the UNIQUE constraint owns that).
    """
    if kind not in ASSESSMENT_KINDS:
        raise ValueError(f"invalid kind {kind!r}; expected {ASSESSMENT_KINDS}")
    if track not in ASSESSMENT_TRACKS:
        raise ValueError(
            f"invalid track {track!r}; expected {ASSESSMENT_TRACKS}"
        )
    result = await session.execute(
        text(
            "INSERT INTO assessments "
            "(slug, kind, track, created_by, created_at) "
            "VALUES (:slug, :kind, :track, :cb, :ts) RETURNING id"
        ),
        {"slug": slug, "kind": kind, "track": track,
         "cb": created_by, "ts": utcnow_iso()},
    )
    new_id = int(result.scalar_one())
    await session.commit()
    return new_id


async def _next_version_number(
    session: AsyncSession, assessment_id: int
) -> int:
    """Return the next monotonic ``version_number`` for *assessment_id*."""
    result = await session.execute(
        text(
            "SELECT COALESCE(MAX(version_number), 0) + 1 "
            "FROM assessment_versions WHERE assessment_id = :a"
        ),
        {"a": assessment_id},
    )
    return int(result.scalar_one())


async def create_draft_version(
    session: AsyncSession,
    *,
    assessment_id: int,
    drafted_by: int,
    questions: list[dict],
) -> int:
    """Insert one draft version + its questions atomically.

    Computes the next ``version_number`` (1 for the first draft).
    Question failures roll back the version row so no orphan survives.
    """
    version_number = await _next_version_number(session, assessment_id)
    try:
        result = await session.execute(
            text(
                "INSERT INTO assessment_versions "
                "(assessment_id, version_number, status, drafted_by, "
                "created_at) VALUES (:a, :vn, 'draft', :db, :ts) "
                "RETURNING id"
            ),
            {"a": assessment_id, "vn": version_number,
             "db": drafted_by, "ts": utcnow_iso()},
        )
        version_id = int(result.scalar_one())
        await insert_questions(session, version_id, questions)
    except Exception:
        await session.rollback()
        raise
    await session.commit()
    return version_id


async def list_pending_reviews(
    session: AsyncSession, *, reviewer_role: str
) -> list[dict]:
    """Return the reviewer queue filtered for *reviewer_role*.

    Joins versions to assessments to apply the track filter. Versions
    in published / retired / rejected / approved are excluded; only
    versions awaiting reviewer action surface.
    """
    tracks = ROLE_TRACK_FILTER.get(reviewer_role)
    if not tracks:
        return []
    sql, binds = build_pending_reviews_sql(tracks)
    result = await session.execute(text(sql), binds)
    return [dict(row._mapping) for row in result]


async def get_version_with_questions(
    session: AsyncSession, version_id: int
) -> dict | None:
    """Return one version + its questions ordered by position, or None.

    Includes ``rubric_json`` because this feeds the *internal* reviewer
    UI; :func:`get_published_version` strips it for public callers.
    """
    version_result = await session.execute(
        text(
            "SELECT id AS version_id, assessment_id, version_number, "
            "status, drafted_by, reviewed_by, approved_by, "
            "published_at, retired_at, created_at "
            "FROM assessment_versions WHERE id = :id"
        ),
        {"id": version_id},
    )
    version_row = version_result.first()
    if version_row is None:
        return None
    questions_result = await session.execute(
        text(
            "SELECT id, position, prompt, kind, rubric_json, scoring_weight "
            "FROM assessment_questions WHERE version_id = :v "
            "ORDER BY position"
        ),
        {"v": version_id},
    )
    payload = dict(version_row._mapping)
    payload["questions"] = [dict(r._mapping) for r in questions_result]
    return payload


async def record_review(
    session: AsyncSession,
    *,
    version_id: int,
    reviewer_id: int,
    action: str,
    comment: str | None,
) -> int:
    """Insert one review row and transition the version's status.

    Raises ``ValueError`` for unknown actions, missing versions, or
    attempts to review a published / retired version. The actual
    INSERT + UPDATE pair lives in :mod:`._assessments_state` to keep
    this function under the per-function size limit.
    """
    if action not in REVIEW_ACTIONS:
        raise ValueError(
            f"invalid action {action!r}; expected {REVIEW_ACTIONS}"
        )
    current_status = await load_version_status(session, version_id)
    if current_status is None:
        raise ValueError(f"version {version_id} does not exist")
    if current_status in IMMUTABLE_STATUSES:
        raise ValueError(
            f"cannot review a {current_status} version (id={version_id})"
        )
    return await insert_review_and_transition(
        session,
        version_id=version_id,
        reviewer_id=reviewer_id,
        action=action,
        comment=comment,
    )


async def publish_version(
    session: AsyncSession, *, version_id: int, approved_by: int
) -> None:
    """Transition *version_id* from ``approved`` to ``published``.

    Raises ``ValueError`` if the version does not exist or its current
    status is anything other than ``approved`` (the state-machine
    guard against bypassing review).
    """
    current_status = await load_version_status(session, version_id)
    if current_status is None:
        raise ValueError(f"version {version_id} does not exist")
    if current_status != "approved":
        raise ValueError(
            f"cannot publish version {version_id} from status "
            f"{current_status!r}; must be approved"
        )
    await session.execute(
        text(
            "UPDATE assessment_versions "
            "SET status = 'published', published_at = :ts, "
            "approved_by = :ab WHERE id = :id"
        ),
        {"ts": utcnow_iso(), "ab": approved_by, "id": version_id},
    )
    await session.commit()


async def get_published_version(
    session: AsyncSession, slug: str
) -> dict | None:
    """Return the latest published version for *slug* with public questions.

    Public payload deliberately EXCLUDES ``rubric_json`` from each
    question — leaking it would let candidates game scoring. Returns
    ``None`` if no version of *slug* has ever been published.
    """
    version_result = await session.execute(
        text(
            "SELECT v.id AS version_id, v.assessment_id, v.version_number, "
            "v.status, v.published_at, a.slug, a.kind, a.track "
            "FROM assessment_versions v "
            "JOIN assessments a ON a.id = v.assessment_id "
            "WHERE a.slug = :slug AND v.status = 'published' "
            "ORDER BY v.version_number DESC LIMIT 1"
        ),
        {"slug": slug},
    )
    version_row = version_result.first()
    if version_row is None:
        return None
    payload = dict(version_row._mapping)
    questions_result = await session.execute(
        text(
            "SELECT id, position, prompt, kind, scoring_weight "
            "FROM assessment_questions WHERE version_id = :v "
            "ORDER BY position"
        ),
        {"v": payload["version_id"]},
    )
    payload["questions"] = [dict(r._mapping) for r in questions_result]
    return payload


async def retire_version(
    session: AsyncSession, *, version_id: int
) -> None:
    """Transition *version_id* to ``retired`` (admin-only path).

    Raises ``ValueError`` if the version does not exist or is already
    retired (prevents accidental double-stamping of ``retired_at``).
    """
    current_status = await load_version_status(session, version_id)
    if current_status is None:
        raise ValueError(f"version {version_id} does not exist")
    if current_status == "retired":
        raise ValueError(f"version {version_id} is already retired")
    await session.execute(
        text(
            "UPDATE assessment_versions "
            "SET status = 'retired', retired_at = :ts WHERE id = :id"
        ),
        {"ts": utcnow_iso(), "id": version_id},
    )
    await session.commit()


__all__ = [
    "create_assessment", "create_draft_version", "list_pending_reviews",
    "get_version_with_questions", "record_review", "publish_version",
    "get_published_version", "retire_version",
]
