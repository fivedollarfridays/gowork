# T13.101 — GDPR-Adjacent Export/Delete Verify

**Sprint:** S13
**Method:** Audit GDPR Articles 15-17 (right of access / rectification / erasure) implementations against the codebase.
**Generated:** 2026-04-25
**Cross-reference:** T13.70 (compliance cascade fix), T13.58 (retention sweep PII fix), T12.36 (S12b compliance gate)

## GDPR Article checklist

| Article | Right | Implementation | Status |
|---------|-------|---------------|--------|
| Art. 15 | Right of access | `compliance.export.build_archive` returns ZIP with `data.json` (every session-scoped row) + `summary.md` | ✓ |
| Art. 16 | Right of rectification | Worker can update profile via `assessment` and per-module endpoints | ✓ (implicit — workers have always-on edit access) |
| Art. 17 | Right of erasure ("right to be forgotten") | `compliance.delete.full_delete` cascades through 14 session-scoped tables (T13.70-hardened) | ✓ |
| Art. 17 | Selective erasure | `compliance.delete.selective_delete` (per-table scope) | ✓ |
| Art. 17 (data retention) | Auto-erase past expiry | `compliance.retention.retention_sweep` purges sessions past `expires_at + 90d` (T13.58-hardened cascade) | ✓ |
| Art. 30 | Records of processing | `compliance_audit` table records every export/delete action with hashed actor + session | ✓ |

## Findings

### M — Public-facing data-rights documentation missing

- **Site:** docs/ has runbooks for ops but no public-facing privacy notice
- **Issue:** GDPR Art. 13-14 require informing data subjects of their rights and how to exercise them. Without `/privacy` and `/terms` pages, judges and pilot users have no statement of rights.
- **Severity:** Medium (T13.115 — privacy + ToS authoring — is on the active backlog; this finding consolidates)
- **Fix:** ship T13.115; ensure it includes a "Your data rights" section listing access (export endpoint), rectification (where workers edit profile), erasure (delete endpoint), portability (export format), and how to contact about data.

### Verified clean

- **Right of access:** `POST /api/compliance/export` returns a signed download token (24h TTL); `GET /api/compliance/download/{token}` returns ZIP. Archive contains `data.json` (every session row from every session-scoped table) + `summary.md` (human-readable). T13.70 schema-introspection verifies completeness.
- **Right of erasure:** `POST /api/compliance/delete` requires confirm="DELETE"; cascade reaches 14 tables (T13.70 hardened); audit row preserved as immutable trail (`compliance_audit` allowlisted from cascade).
- **Selective erasure:** `POST /api/compliance/delete/selective` covers per-module deletion via tombstone columns (`deleted_at` set; reads filter `WHERE deleted_at IS NULL`).
- **Auto-retention:** 90-day grace post-expiry; full cascade (T13.58 fixed the leak in m001 tables).
- **Audit immutability:** `compliance_audit` row written for every export/delete; `hash_session_id` ensures audit retention doesn't itself violate erasure (the audit references hashes, not raw IDs).
- **Token-gated access:** all 3 compliance endpoints require feedback-token auth (session ownership). Cross-session blocked (T13.63).

## Verification (post-T13.70)

The cascade test introspects `sqlite_master` + `PRAGMA foreign_key_list` and asserts `full_delete` clears every session-scoped table. **A new session-scoped table added in a future migration will fail the cascade test in CI**, forcing the developer to either add cascade or document a non-cascade rationale. This drift guard is the strongest GDPR-erasure evidence.

## Recommendation

- Ship T13.115 (privacy + ToS pages) before any external rollout. Already on the active backlog.
- For hackathon submission: judges may inspect `/privacy` and `/terms` — placeholder pages are better than 404s.
- Document data-rights workflow in `docs/architecture.md` so future developers don't break the cascade unintentionally.

## Out of scope

- Cross-border transfer compliance (Schrems II / SCCs) — depends on hosting region; out of scope for hackathon
- Data Protection Impact Assessment (DPIA) — required for high-risk processing in production; defer
- Subprocessor agreements (SendGrid, Anthropic, OpenAI) — needed for prod rollout
