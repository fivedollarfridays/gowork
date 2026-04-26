# T13.102 — Audit Trail Completeness

**Sprint:** S13
**Method:** Inventory every audit-write site; verify mutating endpoints are covered; cross-check with T13.59's contract.
**Generated:** 2026-04-25
**Cross-reference:** T13.59 (audit integrity tests + advisor PII fix), T13.70 (cascade verification)

## Audit infrastructure summary

The codebase uses **multiple audit destinations**, each scoped to its domain:

| Destination | File | Captures |
|-------------|------|----------|
| `compliance_audit` table (m003+m006) | `modules/compliance/_audit.py::write_audit` | export_requested, export_downloaded, export_failed, full_delete, selective_delete, retention_sweep |
| `engagement_events` table (m002) — `advisor_action` event_type | `routes/advisor_inbox.py::_build_audit_payload` (T13.59-hardened with `hash_session_id`) | advisor send-note, advisor view |
| `engagement_events` — `reminders_auto_disabled` event_type | unsubscribe write path | unsubscribe |
| `feature_flag_audit` table (m002) | `core/feature_flags._write_audit_row` | flag toggles |
| `audit_log` (file-based, optional) | `core/audit.py::audit_log` | LLM interactions, configurable via `AUDIT_LOG_PATH` env |
| `bypass_log.jsonl` | `bpsai-pair task update --no-strict --reason ...` | dev workflow bypasses (audited per CLAUDE.md) |

## T13.59 inventory result (already verified)

T13.59 inventoried 34 mutating endpoints: 8 write a DB audit row, 26 are allowlisted with rationale (logger-only via `audit_log`, webhook → `sendgrid_events` not worker-mutation, scaffolding/admin, row-is-the-audit for CRUD on appointments/applications/documents).

**T13.102 confirms the T13.59 inventory is current.** No new mutating endpoints have been added since T13.59 ran.

## Findings

### Verified clean (re-verified post-Wave 4)

- ✓ T13.59's audit-integrity tests still pass (`backend/tests/test_audit_integrity.py`)
- ✓ `hash_session_id` used everywhere (`compliance_audit`, `advisor_inbox`, etc.); no raw session_id in any audit row (T13.59 fix)
- ✓ Audit-before-build pattern locked in for compliance export (S12b 4c8207a + T13.59 test 2)
- ✓ Idempotent retry doesn't double-audit (T13.59 test 3, T13.61 verified for unsubscribe)
- ✓ Cascade preserves `compliance_audit` (T13.70 explicit allowlist)
- ✓ Token-rotation actions are not audited per-call (signature events would be excessive); the action they enable IS audited (e.g., compliance export download)

### Edge-case worth flagging (not a finding)

The `bypass_log.jsonl` is a developer-workflow audit, not an application-runtime audit. It logs `task update --no-strict` and similar AC-bypass actions. This is intentional — the file is appended to by `bpsai-pair` itself, NOT by application code. It does NOT track production access patterns. Worth noting in the team's runbook so it's not confused with the application audit.

### One outstanding follow-up from T13.94

- **2 raw `session_id` log calls in `routes/career_center.py:59,73`** — these are LOGGER calls (stdout / log drain), not audit-row writes. T13.94 flagged them; recommendation: centralize via structlog processor that hashes session_id at event-emit time.

## Audit-trail queryability

The audit data is queryable in 3 ways:

1. **Per-session**: `SELECT * FROM compliance_audit WHERE session_id_hash = ?` — works because the hash is deterministic for any given session_id.
2. **Per-actor**: `SELECT * FROM compliance_audit WHERE actor_hash = ?` — same approach.
3. **Per-action**: `SELECT * FROM compliance_audit WHERE action = ?` — direct index in m003.

For `advisor_action` audits (in `engagement_events`), the same query works against `payload_json->>'session_id_hash'` (post-T13.59 fix).

## Recommendation

- No code changes required for audit completeness.
- The career_center logger fix (T13.94) is the one outstanding item that improves audit-adjacent PII handling.
- For ongoing protection: T13.59's test_audit_integrity coverage guard means new mutating endpoints without audit will fail CI. This is the strongest defense against drift.

## Out of scope

- Tamper-evident audit (HMAC chain) — useful for high-trust environments; not required for hackathon scope
- Real-time audit streaming (to SIEM) — out of scope; T13.121 (Sentry) was cancelled for hackathon
- Audit row retention policy (today they live forever; acceptable for compliance audit) — formalize for prod
