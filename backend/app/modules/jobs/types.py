"""Job application Pydantic model (T12.11).

Shape matches the `job_applications` table from migration m002:
    id, session_id, match_source, match_url, company, role,
    resume_version_id, status, applied_date, created_at.

Enum fields re-use the shared enum from
`app.modules.common.temporal_types` — we do NOT redefine it here.

Composite match linkage note
----------------------------
`matching.JobMatch` has NO `id` field. Callers link a job application to
a match by the composite `(match_source, match_url)` — both are required
and non-null at the `applications.create()` layer. This model does not
enforce non-null itself because the persistence/hydration path must be
able to read historical rows with NULL values; the lifecycle layer owns
the input contract.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from app.modules.common.temporal_types import JobApplicationStatus


class JobApplication(BaseModel):
    """A job application attached to a session, tracked through its lifecycle."""

    id: int | None = None  # None until persisted; SQLite assigns.
    session_id: str
    match_source: str | None = None  # required at create-time; nullable in DB
    match_url: str | None = None     # required at create-time; nullable in DB
    company: str | None = None
    role: str | None = None
    resume_version_id: int | None = None  # FK to resume_versions (S12b)
    status: JobApplicationStatus = JobApplicationStatus.DRAFT
    applied_date: date | None = None
    created_at: datetime | None = None  # Set at persistence time.


__all__ = ["JobApplication"]
