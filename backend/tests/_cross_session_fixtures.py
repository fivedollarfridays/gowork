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
    "GET /api/assessments/{slug}":
        "Public candidate-facing assessment fetch (T23.6); no session_id "
        "input, published versions only, rubric_json stripped.",
    "POST /api/credit/assess":
        "Anonymous self-assessment; no session_id input.",
    "POST /api/assessment/":
        "Creates a new session; no cross-session input possible.",
    "POST /api/auth/magic-link":
        "Public — accepts only an email; no session_id input. "
        "Always returns 202 to defeat enumeration (test_auth_magic_link.py).",
    "GET /api/auth/claim":
        "Account-claim endpoint (T22.8); the magic-link token is "
        "single-use and not a session-bound feedback token, so the "
        "session-A id + session-B token IDOR contract does not apply. "
        "Tested directly by test_auth_claim.py.",
    "GET /api/auth/me":
        "Account-binding read (T22.11); auth is the signed gw_account "
        "cookie, no session_id input. Returns 200-with-null for "
        "anonymous to preserve the anonymous-first invariant. "
        "Tested directly by test_auth_me.py.",
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
        "Admin role-gated (require_role('admin'), T26.4); operator-only "
        "scraper trigger. No session_id input — body is a list of URLs. "
        "Tested directly by test_brightdata_routes.py.",
    "GET /api/brightdata/status/{snapshot_id}":
        "Admin role-gated (require_role('admin'), T26.4); operator-only "
        "scraper status. Path id is a BrightData snapshot id, not a "
        "session_id. Tested directly by test_brightdata_routes.py.",
    "POST /api/brightdata/precrawl":
        "Admin role-gated (require_role('admin'), T26.4); operator-only "
        "scraper trigger. No body, no session_id input. Tested directly "
        "by test_brightdata_routes.py.",
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
    # ---------- S23 assessment authoring (role-gated, not session-scoped)
    "GET /api/admin/assessments/pending":
        "Reviewer role auth (any_of_roles), not session-scoped.",
    "GET /api/admin/assessments/{version_id}":
        "Reviewer role auth (any_of_roles), not session-scoped.",
    "POST /api/admin/assessments/draft":
        "Reviewer role auth (any_of_roles), not session-scoped.",
    "POST /api/admin/assessments/{version_id}/review":
        "Reviewer role auth (any_of_roles), not session-scoped.",
    "POST /api/admin/assessments/{version_id}/publish":
        "Admin role auth (require_role), not session-scoped.",
    # ---------- S24 listing verification (role-gated, not session-scoped)
    "POST /api/employers/claim":
        "Public — accepts {listing_id, claimant_email}; no session_id "
        "input. Always returns 202 to defeat enumeration "
        "(test_employers_claim.py).",
    "GET /api/employers/claim/verify":
        "Listing-claim verify endpoint (T24.4); the claim token is "
        "single-use and not a session-bound feedback token, so the "
        "session-A id + session-B token IDOR contract does not apply. "
        "Tested directly by test_employers_claim_verify.py.",
    "POST /api/listings/{listing_id}/events":
        "Role-gated (any_of_roles case_manager, admin); not "
        "session-scoped. Anonymous candidate session_id may appear in "
        "the body as a free-text reference but auth is the gw_account "
        "cookie, never the body session_id.",
    "POST /api/employers/{employer_account_id}/listings/{listing_id}/intake":
        "Role-gated (gw_employer_account cookie matching the path's "
        "employer_account_id, OR admin role via gw_account cookie). "
        "Not session-scoped — body has no session_id input. Tested "
        "directly by test_employers_intake.py.",
    "GET /api/employers/admin/claims/pending":
        "Admin role-gated (require_role('admin')); not session-scoped. "
        "Tested directly by test_employers_admin.py.",
    "GET /api/employers/admin/claims/{claim_id}":
        "Admin role-gated (require_role('admin')); not session-scoped. "
        "Tested directly by test_employers_admin.py.",
    "POST /api/employers/admin/claims/{claim_id}/approve":
        "Admin role-gated (require_role('admin')); not session-scoped. "
        "Tested directly by test_employers_admin.py.",
    "DELETE /api/employers/admin/claims/{claim_id}":
        "Admin role-gated (require_role('admin')); not session-scoped. "
        "Tested directly by test_employers_admin.py.",
    "GET /api/admin/cities/summary":
        "Admin role-gated (require_role('admin')); read-only diagnostic "
        "page that aggregates per-city seed-file counts. No session_id "
        "input, no DB queries. Tested directly by test_cities_admin.py "
        "(S25 / T25.7).",
    # ---------- S26 admin feedback inbox + flagged-queue (T26.3)
    "GET /api/admin/feedback/flagged":
        "Admin role-gated (require_role('admin')); flagged-resource "
        "queue read. No session_id input — only an optional `?city=` "
        "slug filter. Tested directly by test_admin_feedback.py.",
    "POST /api/admin/feedback/flagged/{resource_id}/approve":
        "Admin role-gated (require_role('admin')); clears a flagged "
        "resource's flag (sets health_status='healthy'). Path id is a "
        "resources.id, not a session_id; no session-scoped IDOR shape. "
        "Tested directly by test_admin_feedback.py.",
    "POST /api/admin/feedback/flagged/{resource_id}/confirm-hide":
        "Admin role-gated (require_role('admin')); soft-hides a "
        "flagged resource (sets health_status='hidden'). Path id is a "
        "resources.id, not a session_id. Tested directly by "
        "test_admin_feedback.py.",
    "GET /api/admin/feedback/visits":
        "Admin role-gated (require_role('admin')); paginated browse "
        "of visit_feedback. No session_id input — only `reviewed`, "
        "`limit`, `offset` query params. Tested directly by "
        "test_admin_feedback.py.",
    "POST /api/admin/feedback/visits/{visit_id}/mark-reviewed":
        "Admin role-gated (require_role('admin')); sets reviewed=1 + "
        "optional action_taken on a visit_feedback row. Path id is a "
        "visit_feedback.id, not a session_id; the body never carries "
        "a session_id. Tested directly by test_admin_feedback.py.",
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
