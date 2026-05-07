"""Public assessment-fetch endpoint (T23.6) — candidate-facing surface.

``GET /api/assessments/{slug}`` is the only candidate-side read of the
assessment authoring pipeline. The route is intentionally:

* **Fully public** — no auth dependency, no session binding. The
  integrity charter forbids forced-login on candidate flows; the
  matching engine and assessment surfaces work without an account.
* **Published-only** — ``queries_assessments.get_published_version``
  filters strictly on ``status='published'``. Drafts, in_review, and
  approved versions are NEVER reachable from this route. A slug with
  no published version returns 404.
* **Rubric-stripped** — the queries-layer helper deliberately omits
  ``rubric_json`` from each question. Leaking rubrics would let
  candidates game scoring; this is the load-bearing privacy invariant
  for the assessment family. Tests in ``test_assessments_public.py``
  (and the queries-layer tests in ``test_queries_assessments_crud``)
  pin the omission both at the SQL helper and at the HTTP boundary.
* **Cacheable** — ``Cache-Control: public, max-age=60`` is set on
  every 200. Published versions are immutable (only superseded by a
  newer version, never mutated in place) so a one-minute edge cache
  is safe.

The route does NOT extend ``app.routes.auth`` — the auth module is
already at its size limit. ``assessments_public_router`` is mounted
in :mod:`app.routes.__init__` alongside the reviewer router.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import queries_assessments
from app.core.database import get_db


router = APIRouter(prefix="/api/assessments", tags=["assessments-public"])


_CACHE_CONTROL = "public, max-age=60"


def _shape_public_payload(raw: dict) -> dict:
    """Project the queries-layer dict to the public response schema.

    The queries helper already strips ``rubric_json`` from each
    question, but it returns extra reviewer-internal fields
    (``version_id``, ``assessment_id``, ``status``) that have no
    business on the candidate surface. We project to the documented
    schema explicitly so future additions to the queries shape don't
    silently leak through this endpoint.
    """
    questions = [
        {
            "position": q["position"],
            "prompt": q["prompt"],
            "kind": q["kind"],
            "scoring_weight": q["scoring_weight"],
        }
        for q in raw["questions"]
    ]
    return {
        "slug": raw["slug"],
        "kind": raw["kind"],
        "track": raw["track"],
        "version_number": raw["version_number"],
        "published_at": raw["published_at"],
        "questions": questions,
    }


@router.get("/{slug}")
async def get_published_assessment(
    slug: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return the latest published version of *slug* + its questions.

    404 if no version of *slug* has ever reached ``status='published'``
    — drafts and approved-but-not-published versions are never
    publicly fetchable. ``Cache-Control: public, max-age=60`` is set
    on every successful response.
    """
    raw = await queries_assessments.get_published_version(db, slug)
    if raw is None:
        raise HTTPException(
            status_code=404,
            detail=f"No published assessment for slug {slug!r}",
        )
    response.headers["Cache-Control"] = _CACHE_CONTROL
    return _shape_public_payload(raw)


__all__ = ["router", "get_published_assessment"]
