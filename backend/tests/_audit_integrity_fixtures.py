"""Endpoint inventory + helpers for audit-integrity tests (T13.59).

Lives outside :mod:`tests.test_audit_integrity` so the test file stays
under the architecture-warning size threshold. The data tables here
are the only mutable inputs to the audit-integrity test — every other
code path in the test module is parameterized over them.

Audit-row contract under test
-----------------------------
For every mutating endpoint that the worker companion exposes, exactly
one of the following audit-row sinks fires per successful call:

* ``compliance_audit`` — written by
  :func:`app.modules.compliance._audit.write_audit`. One row per
  ``(action, session_id_hash)``. Carries no raw session id or PII;
  ``actor_token_hash`` is SHA256-hashed.

* ``engagement_events (category='advisor_action')`` — the advisor inbox
  writes one row per advisor action. Section 10 C4 of the advisor-auth
  runbook anchors the contract; advisor id is hashed in the payload.

* ``engagement_events (category='reminders_auto_disabled')`` — written
  by ``POST /api/engagement/preferences`` (when disabling) and the
  POST/GET unsubscribe handlers. The single-use unsubscribe token guards
  against double-write on retry.

* ``feature_flag_audit`` — written by
  :func:`app.core.feature_flags.set_flag_runtime`. Captures
  ``actor_token_hash`` + ``source_ip`` so the human-side bypass log
  can be cross-correlated with toggle activity.

The CLI ``bypass_log.jsonl`` (under ``.paircoder/history/``) is a
JSONL file maintained by the bpsai-pair toolchain, NOT a runtime audit
sink the FastAPI app writes to. It is intentionally out of scope here.

Allowlist policy
----------------
Every mutating route exposed by the FastAPI app must be triaged into
one of two buckets:

1. ``EXPECTED_AUDIT_SHAPES`` — route is expected to write exactly one
   audit row to the named table. The test exercises the route and
   asserts a +1 delta in that table.

2. ``AUDIT_ALLOWLIST`` — route is intentionally NOT a DB-audit-row
   writer. Each entry MUST carry a one-line rationale; categories:

   * "Logger-only" — emits an :func:`app.core.audit.audit_log`
     structured-log record but no DB row. Outside the DB-row
     integrity contract; covered by ``test_audit.py``.
   * "Webhook" — third-party webhook (SendGrid). Persists raw events
     to ``sendgrid_events`` for replay analysis but is not a session
     mutation that requires a per-call worker-facing audit row.
   * "Admin scaffolding" — demo seed / brightdata crawler triggers.
     Admin-key gated, not part of the worker journey.
   * "No persistence" — pure read-through compute (e.g. simulate,
     pathway, barrier-intel chat). Mutates nothing the runbook calls
     auditable.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuditShape:
    """One mutating endpoint's expected audit-row shape.

    ``table`` — sqlite table that should grow by exactly one row.
    ``category_filter`` — optional WHERE clause (e.g. category =
    'advisor_action') used to disambiguate when the table is shared
    by multiple writers.
    ``action_filter`` — optional WHERE clause for ``compliance_audit``
    (one table, many actions).
    """

    table: str
    category_filter: str | None = None
    action_filter: str | None = None


# Routes that DO write a DB-backed audit row. Keyed by ``"METHOD path"``.
EXPECTED_AUDIT_SHAPES: dict[str, AuditShape] = {
    # ---------- compliance ----------
    "POST /api/compliance/export": AuditShape(
        table="compliance_audit", action_filter="export_requested",
    ),
    "POST /api/compliance/delete": AuditShape(
        table="compliance_audit", action_filter="full_delete",
    ),
    "POST /api/compliance/delete/selective": AuditShape(
        table="compliance_audit", action_filter="selective_delete",
    ),
    # ---------- admin / feature flags ----------
    "POST /api/admin/flags/{name}": AuditShape(
        table="feature_flag_audit",
    ),
    # ---------- advisor inbox (engagement_events as advisor audit) ----------
    "POST /api/advisor/sessions/{session_id}/note": AuditShape(
        table="engagement_events", category_filter="advisor_action",
    ),
    # ---------- engagement (auto-disabled signal) ----------
    "POST /api/engagement/preferences": AuditShape(
        table="engagement_events",
        category_filter="reminders_auto_disabled",
    ),
    "POST /api/engagement/unsubscribe": AuditShape(
        table="engagement_events",
        category_filter="reminders_auto_disabled",
    ),
    "GET /api/engagement/unsubscribe": AuditShape(
        table="engagement_events",
        category_filter="reminders_auto_disabled",
    ),
}


# Mutating routes that intentionally do NOT write a DB audit row.
# Each entry MUST carry a rationale from one of the four categories
# documented in the module header.
AUDIT_ALLOWLIST: dict[str, str] = {
    # ---------- Logger-only audit (audit_log structured log) ----------
    "POST /api/assessment/":
        "Logger-only — emits 'session_created' via app.core.audit.audit_log.",
    "POST /api/credit/assess":
        "Logger-only — emits 'credit_assessed' via app.core.audit.audit_log.",
    "POST /api/feedback/resource":
        "Logger-only — emits 'feedback_resource' via app.core.audit.audit_log.",
    "POST /api/feedback/visit":
        "Logger-only — emits 'feedback_visit' via app.core.audit.audit_log.",
    "POST /api/auth/magic-link":
        "No-persistence audit — credential row IS the audit "
        "(account_credentials, hashed token + 15-min expiry); "
        "always-202 contract precludes per-call audit_log.",
    "POST /api/plan/{session_id}/generate":
        "Logger-only — emits 'plan_generated' via app.core.audit.audit_log.",
    "POST /api/plan/{session_id}/refresh":
        "Logger-only — emits 'plan_refreshed' via app.core.audit.audit_log.",
    "POST /api/plan/{session_id}/share":
        "Logger-only — emits 'plan_shared' via app.core.audit.audit_log.",
    # ---------- Webhook (own audit table) ----------
    "POST /api/webhooks/sendgrid/events":
        "Webhook — persists to sendgrid_events; not a worker-mutation audit.",
    # ---------- Admin scaffolding / internal triggers ----------
    "POST /api/demo/seed":
        "Admin scaffolding — admin-key gated demo bootstrap, no per-call audit.",
    "POST /api/brightdata/crawl":
        "Admin scaffolding — internal scraper trigger.",
    "POST /api/brightdata/precrawl":
        "Admin scaffolding — internal scraper trigger.",
    "POST /api/barrier-intel/reindex":
        "Admin scaffolding — admin-key gated reindex.",
    "POST /api/engagement/send-now":
        "Admin scaffolding — manual send dispatcher; "
        "the resulting reminder write is audited by the reminder engine.",
    # ---------- No-persistence compute / mutations covered elsewhere ----------
    "POST /api/appointments":
        "No-persistence audit — appointment row IS the audit; "
        "transactional emails write engagement_events on send.",
    "POST /api/appointments/from-pathway":
        "No-persistence audit — appointment row IS the audit.",
    "POST /api/appointments/{appointment_id}/attended":
        "Status transition — outcomes_records row written by status_transitions.",
    "POST /api/appointments/{appointment_id}/missed":
        "Status transition — outcomes_records row written by status_transitions.",
    "PATCH /api/appointments/{appointment_id}":
        "No-persistence audit — appointment row IS the audit.",
    "DELETE /api/appointments/{appointment_id}":
        "No-persistence audit — appointment row IS the audit.",
    "POST /api/job-applications":
        "No-persistence audit — application row IS the audit.",
    "PATCH /api/job-applications/{application_id}":
        "No-persistence audit — application row IS the audit.",
    "POST /api/documents/resume":
        "No-persistence audit — version row IS the audit.",
    "POST /api/documents/cover-letter":
        "No-persistence audit — version row IS the audit.",
    "POST /api/pathway":
        "No-persistence compute — pure read-through pathway calculation.",
    "POST /api/simulate":
        "No-persistence compute — pure read-through simulation.",
    "POST /api/barrier-intel/chat":
        "No-persistence compute — streaming LLM response.",
    "POST /api/plan/{session_id}/match/{job_index}/explain":
        "No-persistence compute — Haiku-explained match rationale.",
    "POST /api/plan/{session_id}/next-steps/compose":
        "No-persistence compute — Haiku-composed action sequence.",
    "PATCH /api/plan/{session_id}/actions":
        "Plan mutation — recorded inside plan_history on next refresh.",
    # ---------- S23 assessment authoring ----------
    "POST /api/admin/assessments/draft":
        "No-persistence audit — assessment_versions + assessment_questions "
        "rows ARE the audit (drafted_by + created_at columns).",
    "POST /api/admin/assessments/{version_id}/review":
        "No-persistence audit — assessment_reviews row IS the audit "
        "(reviewer_id, action, comment, created_at).",
    "POST /api/admin/assessments/{version_id}/publish":
        "No-persistence audit — assessment_versions row IS the audit "
        "(approved_by + published_at columns set on publish).",
    # ---------- S24 listing verification ----------
    "POST /api/employers/claim":
        "No-persistence audit — listing_claims row IS the audit "
        "(claim_token_hash + listing_id + claimant_email + 15-min "
        "expiry); always-202 contract precludes per-call audit_log.",
    "POST /api/listings/{listing_id}/events":
        "No-persistence audit — listing_reputation_events row IS the "
        "audit (recorded_by + occurred_at columns set on insert); "
        "the event stream is itself the append-only audit log.",
    "POST /api/employers/{employer_account_id}/listings/{listing_id}/intake":
        "No-persistence audit — listing_verifications row IS the audit "
        "(intake_json + intake_completed_at columns stamped on submit); "
        "role-gated (gw_employer_account cookie matching path or admin "
        "role override).",
    "POST /api/employers/admin/claims/{claim_id}/approve":
        "No-persistence audit — employer_accounts.verified_at + "
        "verification_status='verified' columns ARE the audit; "
        "admin role-gated (require_role('admin')).",
    "DELETE /api/employers/admin/claims/{claim_id}":
        "No-persistence audit — employer_accounts.verification_status="
        "'retired' is the audit trail for the rejection; admin "
        "role-gated (require_role('admin')).",
    # ---------- S26 admin feedback inbox + flagged-queue (T26.3)
    "POST /api/admin/feedback/flagged/{resource_id}/approve":
        "No-persistence audit — resources.health_status flip "
        "('flagged' -> 'healthy') IS the audit; admin role-gated "
        "(require_role('admin')). Tested directly by "
        "test_admin_feedback.py.",
    "POST /api/admin/feedback/flagged/{resource_id}/confirm-hide":
        "No-persistence audit — resources.health_status flip "
        "('flagged' -> 'hidden') IS the audit (soft-delete preserves "
        "the row + its referencing feedback for audit replay); admin "
        "role-gated (require_role('admin')). Tested directly by "
        "test_admin_feedback.py.",
    "POST /api/admin/feedback/visits/{visit_id}/mark-reviewed":
        "No-persistence audit — visit_feedback.reviewed + "
        "action_taken columns ARE the audit (set on flip; the row "
        "itself is the operator-action record); admin role-gated "
        "(require_role('admin')). Tested directly by "
        "test_admin_feedback.py.",
    # ---------- S26 admin resource CRUD (T26.2)
    "POST /api/admin/resources":
        "No-persistence audit — resources row IS the audit "
        "(user_curated_at column stamped server-side on every create); "
        "admin role-gated (require_role('admin')). Tested directly by "
        "test_admin_resources.py.",
    "PATCH /api/admin/resources/{resource_id}":
        "No-persistence audit — resources.user_curated_at column "
        "stamped server-side on every patch IS the audit (touch-as-"
        "curation semantic); admin role-gated (require_role('admin')). "
        "Tested directly by test_admin_resources.py.",
    "DELETE /api/admin/resources/{resource_id}":
        "No-persistence audit — resources.health_status flip to "
        "'hidden' IS the audit (soft-delete preserves the row + its "
        "referencing feedback for audit replay); admin role-gated "
        "(require_role('admin')). Tested directly by "
        "test_admin_resources.py.",
    "POST /api/admin/resources/{resource_id}/restore":
        "No-persistence audit — resources.health_status flip back to "
        "'healthy' IS the audit (reverses a prior soft-delete); admin "
        "role-gated (require_role('admin')). Tested directly by "
        "test_admin_resources.py.",
}


__all__ = [
    "AUDIT_ALLOWLIST",
    "AuditShape",
    "EXPECTED_AUDIT_SHAPES",
]
