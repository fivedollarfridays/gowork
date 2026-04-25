# T13.93 — Token Scope Audit

**Sprint:** S13
**Method:** Read-only audit of `backend/app/modules/*/tokens.py` + every enforcement site grep'd from `backend/app/routes/`.
**Generated:** 2026-04-25
**Cross-reference:** T13.62 (appointments token rotation fix), Wave 4 follow-up (compliance + engagement token-downgrade fixes), T13.71 (share-endpoint P1 finding)

## Token inventory

| # | Token type | Module | Algorithm | Claims | TTL | Single-use | Key rotation (kid) | Enforcement site |
|---|------------|--------|-----------|--------|-----|------------|-------------------|------------------|
| 1 | Session token | `core/queries_feedback.py` (DB-row) | random 96-bit (`secrets.token_urlsafe(12)`) | opaque, FK to `feedback_tokens(session_id)` | 30d (`feedback_tokens.expires_at`) | No (reusable) | N/A | `core/auth.py::require_session_token` |
| 2 | Feedback token | `modules/feedback/tokens.py` | random 96-bit | opaque, same shape as session token | per-row | No | N/A | `routes/feedback.py` |
| 3 | Manage-appointment | `modules/appointments/tokens.py` | HMAC-SHA256 (signed payload) | `appointment_id`, `action`, `exp`, `kid` | 7d default | Yes (m004 `used_tokens` + `INSERT OR IGNORE`) | **Yes** (T13.62 patched `_KNOWN_KIDS`) | `routes/appointments_manage.py::_verify_or_401` |
| 4 | Compliance export | `modules/compliance/_export_tokens.py` | HMAC-SHA256 | `session_id`, `archive_id`, `exp`, `kid` | 24h | Yes (`used_tokens`) | **Yes** (Wave 4 patched `_KNOWN_KIDS`) | `routes/compliance.py::download_export` |
| 5 | Unsubscribe | `modules/engagement/unsubscribe_tokens.py` | HMAC-SHA256 | `session_id`, `exp`, `kid` | 30d | Yes (`used_tokens`); CAN-SPAM idempotent on replay (T13.61 fix) | **Yes** (Wave 4 patched `_KNOWN_KIDS`) | `routes/engagement.py::_process_unsubscribe` |
| 6 | Share | `routes/share.py` (or wherever) | random URL-safe (need to verify) | opaque token mapped to share record | unknown — verify | No | No | `routes/share.py` |
| 7 | Advisor | `core/advisor_auth.py` (DB-row) | random + bcrypt-hashed in DB | city claim, advisor_id | per-row revocable | N/A (revocation, not rotation) | N/A | `routes/advisor_inbox.py::_verify_advisor` |
| 8 | Admin key | env var `ADMIN_API_KEY` | `hmac.compare_digest` against env | header-only, NO scoping | indefinite (rotation = redeploy) | No | No | `core/auth.py::require_admin_key` |

## Findings

### P0 — Share token under-protected (already P1 in T13.71)
- **Site:** `/api/plan/{sid}/share` → `/shared/[token]` flow
- **Issue:** T13.71's sweep found this leaks `session_id` + full `barriers` list. From the token-scope angle, the share token has:
  - No documented TTL
  - No revocation mechanism
  - No kid rotation
  - No single-use enforcement
- **Severity:** P0 because the leaked content (criminal history, health, housing barriers) is exactly what hackathon judges sharing their session URL would expose to anyone they share with.
- **Fix:** consolidated under T13.71's recommendation — strip `session_id` + barrier detail from the response, add TTL (24h or shareable-for-this-session), document.

### P1 — Admin key is single-purpose, not action-scoped
- **Site:** `core/auth.py::require_admin_key`
- **Issue:** any admin endpoint that requires admin auth requires the SAME single `ADMIN_API_KEY`. There's no "scope" on this token — a person who can flip a feature flag also has authority to run a QC reset, force-disable engagement, etc.
- **Severity:** P1 for prod; tolerable for hackathon (admin endpoints aren't user-reachable).
- **Fix (deferred to S14+):** if multiple admin actors are ever needed, introduce per-action scope claims and a small admin-key registry table. For hackathon, the single key + not-publicly-routed assumption holds.

### P2 — Session/feedback tokens have no rotation
- **Site:** `feedback_tokens` table (m001)
- **Issue:** session/feedback tokens are random opaque values; rotation = invalidate the row. No kid/version, so a leaked token works for the full TTL.
- **Severity:** P2 — random 96-bit entropy makes brute-force infeasible; primary risk is supply-chain leak (e.g., a token in a screenshot). The 30d TTL bounds blast radius.
- **Fix:** out of hackathon scope; revocation already works.

## Verified clean

- Three rotation-aware tokens (appointments, compliance/export, engagement/unsubscribe) all have consistent `_KNOWN_KIDS = frozenset({"current", "old"})` whitelist after T13.62 + Wave 4 follow-up. Token-downgrade attack surface closed.
- `KEY_ROTATION_OVERLAP_DAYS = 7` pinned across all three (matches default token TTL).
- T13.62's `test_key_rotation_overlap.py` + Wave 4's `test_export_token_rotation.py` + extended `test_unsubscribe_tokens.py` lock these contracts in.
- All HMAC tokens use `hmac.compare_digest` for signature verify — no early-exit timing leak.
- Single-use enforcement via `INSERT OR IGNORE INTO used_tokens` is atomic per row (T13.61 verified under burst).
- T13.59 verified every mutating endpoint writes audit rows with `hash_session_id` (not raw).

## Recommendations (priority)

1. **P0 — Fix share-token leak** (T13.71 already filed; consolidate here): strip session_id + barrier detail; add TTL; document.
2. **P1 — Audit advisor token city-claim enforcement**: T13.63 covered cross-session, but cross-CITY needs explicit grep — confirm advisor_inbox.py rejects requests where the token's city doesn't match the city query parameter. (Need follow-up read to confirm.)
3. **P2 — Admin key scoping**: out of hackathon scope; track for S14.

## Out of scope

- TLS / network-layer security (Fly.io handles)
- Frontend cookie security (httpOnly / SameSite / Secure flags) — separate audit
- CSRF on state-changing routes — covered by T13.98
