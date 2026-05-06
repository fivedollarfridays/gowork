"""Allowlist + placeholder data for the cross-session isolation suite (T13.63).

Lifted out of :mod:`tests.test_cross_session_isolation` to keep the test
file under the architecture warning threshold. The data tables here are
the only mutable inputs to the cross-session test — every other code
path in the test module is parameterized over them.

PUBLIC_ENDPOINTS
----------------
Allowlist of ``"METHOD /path"`` keys that the cross-session test does
NOT exercise. Each entry MUST carry a one-line rationale; entries
without a rationale will fail review. Categories of rationale:

* "Path-id ownership covered by ``test_<file>.py``" — the route accepts
  a token only (no ``session_id`` query / body) and verifies ownership
  against an existing path-id resource. The unit-test file listed gives
  full coverage of the cross-session path with a seeded resource.
* "Auth via signed <kind> token" — the route's auth is a single-use or
  share token, not a session-scoped feedback token.
* "Admin-key gated" / "Advisor auth" — different trust boundary.
* "Public" / "Aggregate stats" — no session_id input at all.

REQUIRED_FIELD_PLACEHOLDERS
---------------------------
For each required body field that's NOT ``session_id`` or ``token`` /
``session_token``, a placeholder value that satisfies Pydantic
validation. The cross-session test never wants to fail on a
schema-level 422 — it must reach the ownership check inside the
endpoint. Add new entries here when a new endpoint with required body
fields is introduced.
"""
from __future__ import annotations

from typing import Any


PUBLIC_ENDPOINTS: dict[str, str] = {
    # ---------- Path-id resources (ownership tested in dedicated suites)
    "GET /api/appointments/{appointment_id}":
        "Path-id ownership covered by test_appointments_routes.py.",
    "PATCH /api/appointments/{appointment_id}":
        "Path-id ownership covered by test_appointments_routes.py.",
    "DELETE /api/appointments/{appointment_id}":
        "Path-id ownership covered by test_appointments_routes.py.",
    "POST /api/appointments/{appointment_id}/attended":
        "Path-id ownership covered by test_appointments_routes.py.",
    "POST /api/appointments/{appointment_id}/missed":
        "Path-id ownership covered by test_appointments_routes.py.",
    "PATCH /api/job-applications/{application_id}":
        "Path-id ownership covered by test_jobs_applications_routes.py.",
    "GET /api/documents/resume/{version_id}":
        "Path-id ownership covered by test_documents_routes.py.",
    "GET /api/documents/resume/{version_id}/pdf":
        "Path-id ownership covered by test_documents_routes.py.",
    "GET /api/documents/cover-letter/{version_id}":
        "Path-id ownership covered by test_documents_routes.py.",
    "GET /api/documents/cover-letter/{version_id}/pdf":
        "Path-id ownership covered by test_documents_routes.py.",
    # ---------- Token-only routes (no session_id input)
    "GET /api/job-applications/community-funnel":
        "Token-only; resolves city from caller's session, never inputs.",
    "POST /api/feedback/visit":
        "Token-only auth; session_id is derived from the token itself.",
    "GET /api/feedback/validate/{token}":
        "Token-only validation endpoint; no session_id input.",
    # ---------- Public / probes
    "GET /":
        "Public root.",
    "GET /health":
        "Health probe — no session context.",
    "GET /health/live":
        "Health probe — no session context.",
    "GET /health/ready":
        "Health probe — no session context.",
    "GET /health/demo":
        "Health probe — demo freshness check, no session context.",
    "GET /api/city":
        "Public city config.",
    "GET /api/jobs/":
        "Public job listings.",
    "GET /api/jobs/{job_id}":
        "Public job listing detail.",
    "POST /api/credit/assess":
        "Anonymous self-assessment; no session_id input.",
    "POST /api/assessment/":
        "Creates a new session; no cross-session input possible.",
    "POST /api/auth/magic-link":
        "Public — accepts only an email; no session_id input. "
        "Always returns 202 to defeat enumeration (test_auth_magic_link.py).",
    "GET /api/demo/personas":
        "Public demo endpoint — lists canonical personas, no session_id.",
    "GET /api/demo/walkthrough":
        "Public demo endpoint — canned walkthrough payload, no session_id.",
    "GET /api/dashboard/stats":
        "Aggregate stats; no session_id input.",
    "GET /api/outcomes/aggregate":
        "Aggregate outcomes; no session_id input.",
    "GET /api/intelligence/barriers":
        "Aggregate barrier intel; no session_id input.",
    # ---------- Admin / signed-token / webhook auth (different boundary)
    "POST /api/admin/flags/{name}":
        "Admin-key gated, not session-scoped.",
    "POST /api/brightdata/crawl":
        "Admin/internal scraper trigger.",
    "GET /api/brightdata/status/{snapshot_id}":
        "Admin/internal scraper status.",
    "POST /api/brightdata/precrawl":
        "Admin/internal scraper trigger.",
    "POST /api/barrier-intel/reindex":
        "Admin-key gated reindex.",
    "POST /api/demo/seed":
        "Admin-only demo bootstrap.",
    "POST /api/engagement/send-now":
        "Admin-key gated; not session-scoped.",
    "POST /api/engagement/unsubscribe":
        "Public — auth via signed unsubscribe token, no session_id.",
    "GET /api/engagement/unsubscribe":
        "Public — auth via signed unsubscribe token, no session_id.",
    "POST /api/webhooks/sendgrid/events":
        "Webhook; auth via signed webhook key.",
    "GET /api/compliance/export/download":
        "Auth via single-use signed download token, no session_id input.",
    "GET /api/appointments/manage":
        "Auth via signed manage-appointment token, no session_id input.",
    "GET /api/plan/shared/{share_token}":
        "Public share link; auth via the share token itself.",
    "GET /api/advisor/stalled-sessions":
        "Advisor auth, separate trust boundary (test_advisor_auth.py).",
    "GET /api/advisor/sessions/{session_id}":
        "Advisor auth, separate trust boundary (test_advisor_auth.py).",
    "POST /api/advisor/sessions/{session_id}/note":
        "Advisor auth, separate trust boundary (test_advisor_auth.py).",
}


REQUIRED_FIELD_PLACEHOLDERS: dict[str, Any] = {
    # /api/appointments POST body
    "type": "dmv",
    "title": "placeholder",
    "status": "scheduled",
    # /api/compliance/delete + delete/selective
    "confirm": "DELETE",
    "category": "criminal_record",
    # /api/feedback/resource
    "resource_id": 1,
    "helpful": True,
    # /api/job-applications POST
    "match_source": "manual",
    "match_url": "https://example.com/job/1",
    # /api/documents/cover-letter
    "resume_version_id": 1,
    "job_match_ref": {"company": "x", "role": "y"},
    # /api/engagement/preferences
    "reminders_enabled": False,
    # /api/plan/{session_id}/actions — body validates ``key:digit`` shape.
    "action_key": "fix_credit:1",
    "completed": True,
    # /api/barrier-intel/chat — ``mode`` is a closed enum.
    "user_question": "hello",
    "mode": "next_steps",
}


__all__ = ["PUBLIC_ENDPOINTS", "REQUIRED_FIELD_PLACEHOLDERS"]
