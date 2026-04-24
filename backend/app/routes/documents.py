"""Documents API router (T12.17) — resume + cover letter generation.

Seven endpoints under ``/api/documents``:

- POST /api/documents/resume                       — generate via T12.15
- GET  /api/documents/resume/{version_id}           — markdown
- GET  /api/documents/resume/{version_id}/pdf       — PDF (T12.4 renderer)
- POST /api/documents/cover-letter                  — generate via T12.16
- GET  /api/documents/cover-letter/{version_id}     — markdown
- GET  /api/documents/cover-letter/{version_id}/pdf — PDF
- GET  /api/documents/versions?session_id=X         — newest-first list

Auth contract mirrors T12.10 / T12.13: ``token`` query-param backed by
``feedback_tokens``. Every read of a specific version cross-checks the
owning ``session_id`` against the authenticated session (403 otherwise).

Persistence reads run through :mod:`app.modules.documents._versions_db`
(spoke) so the use-counter hook in
:mod:`app.routes.jobs_applications` and the routes layer share one
implementation. Production-time POSTs persist via the existing
T12.15 / T12.16 builders without re-implementing the SQL here.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel

from app.core.pdf_renderer import PdfRenderError, render_markdown_to_pdf
from app.modules.documents import _versions_db as versions_db
from app.modules.documents import cover_letter_builder, resume_builder
from app.routes import _appointments_helpers as _h

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

_DOC_RESUME = "resume"
_DOC_COVER = "cover_letter"
_PDF_TEMPLATE = "default"


# -------------------- Helpers --------------------


def _resolve_db_path() -> str:
    """Indirection so tests can monkeypatch the DB path in one place."""
    return _h.resolve_db_path()


def _load_owned_version(
    version_id: int, session_id: str, *, doc_type: str, db_path: str,
) -> versions_db.ResumeVersion:
    """Fetch a version row; 404 if missing/wrong-type, 403 if cross-session."""
    version = versions_db.get_version(version_id, db_path=db_path)
    if version is None or version.doc_type != doc_type:
        raise HTTPException(status_code=404, detail="Document version not found")
    if version.session_id != session_id:
        raise HTTPException(
            status_code=403,
            detail="Document belongs to another session",
        )
    return version


def _markdown_response(version: versions_db.ResumeVersion) -> Response:
    """Return the markdown body with a ``text/markdown`` content-type."""
    return Response(content=version.markdown, media_type="text/markdown")


def _pdf_response(version: versions_db.ResumeVersion) -> Response:
    """Render the markdown to PDF and return ``application/pdf`` bytes."""
    try:
        pdf_bytes = render_markdown_to_pdf(
            version.markdown, template_name=_PDF_TEMPLATE,
        )
    except PdfRenderError:
        logger.exception(
            "documents_pdf_render_failed",
            extra={"version_id": version.id},
        )
        raise HTTPException(
            status_code=500, detail="PDF rendering failed",
        ) from None
    return Response(content=pdf_bytes, media_type="application/pdf")


# -------------------- Request bodies --------------------


class ResumeCreateBody(BaseModel):
    """POST body for ``/resume``. ``job_description`` is optional context."""

    session_id: str
    job_description: str | None = None


class CoverLetterCreateBody(BaseModel):
    """POST body for ``/cover-letter`` — needs the resume lineage + match."""

    session_id: str
    resume_version_id: int
    job_match_ref: dict[str, Any]


# -------------------- Resume endpoints --------------------


@router.post("/resume", status_code=201)
def post_resume(
    body: ResumeCreateBody, token: str = Query(...),
) -> dict[str, Any]:
    """Generate + persist one resume version, return its identifiers."""
    db_path = _resolve_db_path()
    _h.verify_token(db_path, body.session_id, token)
    draft = resume_builder.generate_resume(
        body.session_id,
        job_description=body.job_description,
        db_path=db_path,
    )
    versions = versions_db.list_versions(
        body.session_id, doc_type=_DOC_RESUME, db_path=db_path,
    )
    latest = versions[0]  # newest-first; the just-persisted row
    return {
        "version_id": latest.id,
        "version_counter": draft.version_counter,
        "session_id": draft.session_id,
        "doc_type": _DOC_RESUME,
        "generation_method": draft.generation_method,
    }


@router.get("/resume/{version_id}")
def get_resume_markdown(
    version_id: int, token: str = Query(...),
) -> Response:
    """Return one resume version as ``text/markdown``."""
    db_path = _resolve_db_path()
    session_id = _h.resolve_session_from_token(db_path, token)
    version = _load_owned_version(
        version_id, session_id, doc_type=_DOC_RESUME, db_path=db_path,
    )
    return _markdown_response(version)


@router.get("/resume/{version_id}/pdf")
def get_resume_pdf(version_id: int, token: str = Query(...)) -> Response:
    """Return the resume rendered to PDF via the T12.4 SSRF-guarded renderer."""
    db_path = _resolve_db_path()
    session_id = _h.resolve_session_from_token(db_path, token)
    version = _load_owned_version(
        version_id, session_id, doc_type=_DOC_RESUME, db_path=db_path,
    )
    return _pdf_response(version)


# -------------------- Cover-letter endpoints --------------------


@router.post("/cover-letter", status_code=201)
def post_cover_letter(
    body: CoverLetterCreateBody, token: str = Query(...),
) -> dict[str, Any]:
    """Generate + persist one cover-letter version, return its identifiers."""
    db_path = _resolve_db_path()
    _h.verify_token(db_path, body.session_id, token)
    draft = cover_letter_builder.generate_cover_letter(
        body.session_id,
        body.job_match_ref,
        body.resume_version_id,
        db_path=db_path,
    )
    versions = versions_db.list_versions(
        body.session_id, doc_type=_DOC_COVER, db_path=db_path,
    )
    latest = versions[0]
    return {
        "version_id": latest.id,
        "version_counter": draft.version_counter,
        "session_id": draft.session_id,
        "doc_type": _DOC_COVER,
        "generation_method": draft.generation_method,
        "fair_chance": draft.fair_chance,
    }


@router.get("/cover-letter/{version_id}")
def get_cover_letter_markdown(
    version_id: int, token: str = Query(...),
) -> Response:
    """Return one cover-letter version as ``text/markdown``."""
    db_path = _resolve_db_path()
    session_id = _h.resolve_session_from_token(db_path, token)
    version = _load_owned_version(
        version_id, session_id, doc_type=_DOC_COVER, db_path=db_path,
    )
    return _markdown_response(version)


@router.get("/cover-letter/{version_id}/pdf")
def get_cover_letter_pdf(
    version_id: int, token: str = Query(...),
) -> Response:
    """Return the cover-letter rendered to PDF."""
    db_path = _resolve_db_path()
    session_id = _h.resolve_session_from_token(db_path, token)
    version = _load_owned_version(
        version_id, session_id, doc_type=_DOC_COVER, db_path=db_path,
    )
    return _pdf_response(version)


# -------------------- Versions list --------------------


@router.get("/versions")
def list_versions_for_session(
    session_id: str = Query(...), token: str = Query(...),
) -> list[dict[str, Any]]:
    """Newest-first list of every doc version owned by the session."""
    db_path = _resolve_db_path()
    _h.verify_token(db_path, session_id, token)
    rows = versions_db.list_versions(session_id, db_path=db_path)
    return [
        {
            "version_id": row.id,
            "session_id": row.session_id,
            "doc_type": row.doc_type,
            "version_counter": row.version_counter,
            "generation_method": row.generation_method,
            "use_counter": row.use_counter,
            "created_at": row.created_at,
        }
        for row in rows
    ]
