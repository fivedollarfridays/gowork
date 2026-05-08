# Sprint 24 — Two-Sided Listing Verification

**Plan type:** feature
**Sprint:** 24
**Total Cx:** 205
**Tasks:** 11 (P0: 10, P1: 1, P2: 0)
**Brief:** `.paircoder/plans/briefs/brief-sprint-24-listing-verification.md`
**Builds on:** Sprint 22 (accounts/sessions/credentials/roles, magic-link auth, anonymous-first invariant, alembic chain through 0012). Sprint 23 (assessment authoring substrate, RoleGate component, useAccountRoles hook, alembic 0013).

## Goal

Stand up the **anti-fake-listing core** and the first paid revenue surface (per-verified-listing fee). Employers prove a listing is theirs via a domain-email claim flow (mirrors the S22 magic-link pattern); the verified employer fills out a structured intake; reputation signals (response rate, withdrawal rate, placement count) are recorded as events. Public job-listing fetches surface a verification-tier badge so candidates see which listings have been claimed and stood behind.

This is the **substrate**. Sprints 25–27 fill it with content (vocational/DAO-tech assessments, gamification mechanics that read reputation rates), and Sprint 30 adds the actual billing/payment integration.

## What ships in S24 vs deferred

**S24 (this sprint):** Schema for employer_accounts / listing_claims / listing_verifications / listing_reputation_events. CRUD modules. Listing-claim initiation (POST) + verification (GET) + employer intake (POST) endpoints — magic-link-style domain-email proof. Public listing fetch extended with verification-tier field (intake_json never publicly leaked). Reputation event recording API. On-demand rate computation. Admin claim-review dashboard for domain-mismatch escalations. Frontend `<VerifiedBadge />` component integrated into existing job-listing UI. Integration gate with explicit charter-integrity test (verification signals NEVER read by the matching engine).

**Deferred to S25+:** Per-verified-listing fee billing/payment integration (S30). Listing reputation EROSION mechanism — withdrawal-penalty UX visible to employers (S26 or S27). Employer self-service dashboard for ongoing listing management (claim + intake is enough this sprint). Multi-tenant employer cohorts (S30). Deep DNS-ownership verification (just SMTP domain match for now). Reputation event ingest from external integrations (manual case-manager records only). Migration of `employer_policies` to FK against `employer_accounts` (orthogonal cleanup). Vocational + DAO-tech assessment authoring (S25/S26).

## Architectural principles

- **`auth.py` 314-line ceiling.** Hard cap 400. Sprint 24 must NOT extend it. Employer + listing-verification routes land in their own modules: `routes/employers.py`, `routes/listing_reputation.py`. Public listing fetch extension lives in the existing `routes/jobs.py` (140 lines — headroom available).
- **Anonymous-first invariant.** The existing `GET /api/jobs` does not require auth. The verification-tier extension MUST keep that property. T22.9's auto-discovery test catches drift on every push.
- **Charter compliance — load-bearing.** Verification tier is computed from artifacts (source-trust + claim + intake completeness + reputation events), NEVER from money. The verified badge is display-only — the matching engine reads ZERO verification signals. Integration gate (T24.11) explicitly grep-tests this.
- **No modification to `job_listings` or ingest adapters.** Verification is parallel; `listing_verifications` carries the metadata. Avoids S22-style migration churn this sprint.
- **`employer_policies` stays as-is.** Existing matching-engine consumers continue using it. Future sprint can consolidate.
- **Single source of truth for ENUMs.** Module-level tuples in `listings_verification_schema.py` (mirrors S23 `assessments_schema.py` pattern).

---

## Phase 1: Foundation — schema + CRUD

### T24.1 — Alembic migration: employer_accounts + listing_claims + listing_verifications + listing_reputation_events | Cx: 25 | P0

**Description:**
Add the four-table verification substrate. Alembic revision 0014 with `down_revision='0013'`. Uses SQLAlchemy Core MetaData mirroring S22+S23 pattern — shared `accounts_schema.metadata` so FKs resolve at create_all time. ENUM constraints via portable CHECK clauses sourced from module-level tuples.

The four tables are parallel to (not a replacement for) the existing `job_listings` and `employer_policies` tables — verification metadata lives separately so this sprint does not churn the matching engine's substrate.

**AC:**
- [ ] `backend/alembic/versions/0014_listing_verification.py` (revision 0014, down_revision 0013)
- [ ] `backend/app/core/listings_verification_schema.py` defines four `Table` objects on shared `accounts_schema.metadata`
- [ ] `employer_accounts(id PK, name UNIQUE, domain, verification_status, verified_at NULL, verified_by_account_id FK accounts NULL, retired_at NULL, source_trust_tier, created_at)`
- [ ] `listing_claims(id PK, claim_token_hash UNIQUE, listing_id FK job_listings, employer_account_id FK NULL, claimant_email, claimant_account_id FK accounts NULL, expires_at, used_at NULL, created_at)`
- [ ] `listing_verifications(listing_id FK job_listings UNIQUE, employer_account_id FK, verification_tier, intake_completed_at NULL, intake_json TEXT NULL, verified_at, created_at)` — UNIQUE on listing_id (one verification per listing)
- [ ] `listing_reputation_events(id PK, listing_id FK, event_kind, session_id NULL, occurred_at, recorded_by FK accounts NULL, notes TEXT NULL)`
- [ ] `verification_status` ENUM via CHECK: `pending | claimed | admin_review | verified | retired`
- [ ] `verification_tier` ENUM via CHECK: `source_trust | claim_verified | admin_reviewed`
- [ ] `event_kind` ENUM via CHECK: `response_received | withdrawn | placed | ghosted`
- [ ] `source_trust_tier` ENUM via CHECK: `unknown | brightdata | honestjobs | twc | manual` (matches existing `job_listings.source` values)
- [ ] Module-level tuples are the single source of truth: `VERIFICATION_STATUSES`, `VERIFICATION_TIERS`, `EVENT_KINDS`, `SOURCE_TRUST_TIERS`
- [ ] `apply_ddl(connection)` helper scoped to the four tables
- [ ] Index on `(listing_id, occurred_at DESC)` on `listing_reputation_events` for the rolling-window reputation hot path
- [ ] `alembic upgrade head` runs clean on fresh sqlite + postgres
- [ ] `bpsai-pair arch check backend/app/core/listings_verification_schema.py` passes

**Depends on:** none

---

### T24.2 — queries_employers.py + queries_listings_verification.py + queries_listings_reputation.py CRUD modules | Cx: 25 | P0

**Description:**
Three CRUD modules consumed by every backend endpoint in this sprint. Async SQLAlchemy with `text()` + named bind params (driver-agnostic). Status transitions enforced at the query layer. State-machine guards: claim must be unused + unexpired before mark_claim_used; verification can transition source_trust → claim_verified → admin_reviewed (one-way, no downgrade).

**AC:**
- [ ] `backend/app/core/queries_employers.py`:
  - [ ] `create_employer_account(session, *, name, domain) -> int`
  - [ ] `get_employer_by_domain(session, domain) -> dict | None`
  - [ ] `get_employer_by_id(session, employer_id) -> dict | None`
  - [ ] `list_pending_admin_review(session) -> list[dict]` — listings whose verification_tier is admin_review
- [ ] `backend/app/core/queries_listings_verification.py`:
  - [ ] `mint_listing_claim_token(session, *, listing_id, claimant_email, claimant_account_id) -> tuple[str, int]` — returns (raw_token, claim_id); SHA-256 hash stored, 15-min expiry
  - [ ] `find_unused_claim_by_hash(session, *, token_hash) -> dict | None` — single helper; returns None for any failure mode (not found / expired / used)
  - [ ] `mark_claim_used(session, claim_id) -> None`
  - [ ] `create_verification(session, *, listing_id, employer_account_id, tier, verified_by) -> None` — UNIQUE on listing_id raises IntegrityError translatable to 409
  - [ ] `set_intake(session, *, listing_id, intake_json) -> None`
  - [ ] `get_verification_for_listing(session, listing_id) -> dict | None`
  - [ ] `get_public_verification_summary(session, listing_ids: list[int]) -> dict[int, dict]` — batched read for the public fetch hot path; intake_json EXCLUDED (only `intake_complete: bool` surfaces)
- [ ] `backend/app/core/queries_listings_reputation.py`:
  - [ ] `record_event(session, *, listing_id, event_kind, recorded_by, session_id=None, notes=None) -> int`
  - [ ] `get_signal_rates(session, listing_id, window_days=30) -> dict` — see T24.8
  - [ ] `aggregate_for_employer(session, employer_account_id, window_days=30) -> dict`
- [ ] State-machine guards raise ValueError; route layer translates to 409
- [ ] All queries portable on sqlite + postgres (text() + named binds + RETURNING id)
- [ ] `backend/tests/test_queries_employers.py` (10+ tests)
- [ ] `backend/tests/test_queries_listings_verification.py` (15+ tests covering claim mint/find/use, verification create/upgrade-tier, intake set, summary batch read)
- [ ] `backend/tests/test_queries_listings_reputation.py` (8+ tests)
- [ ] `bpsai-pair arch check` passes on touched files

**Depends on:** T24.1

---

## Phase 2: Backend pipeline — claim / verify / intake / public surface / reputation

### T24.3 — Listing claim initiation endpoint | Cx: 20 | P0

**Description:**
`POST /api/employers/claim {listing_id, claimant_email}` accepts an email, mints a single-use token, sends a magic-link-style claim URL via SendGrid. Always returns 202 Accepted (no enumeration). Rate-limited tighter than candidate magic-link since this is employer-side. Domain heuristic: extract domain from `claimant_email`; if it fuzzy-matches `job_listings.company`, route to claim_verified tier on subsequent verify; otherwise route to admin_review queue.

Lands in NEW route module — must NOT extend `auth.py`.

**AC:**
- [ ] `backend/app/routes/employers.py` (new) exposes `POST /api/employers/claim`
- [ ] Request body: `{listing_id: int, claimant_email: str}`; response: 202 Accepted (always, no body)
- [ ] Token: `secrets.token_urlsafe(32)` (≥256-bit entropy); SHA-256 hashed in `claim_token_hash`
- [ ] Token expires 15 minutes from issuance; single-use
- [ ] Domain heuristic: extract domain from claimant_email; lookup or auto-create `employer_accounts` row keyed by domain. If `job_listings.company` doesn't fuzzy-match the domain, mark the prospective claim with verification_tier=admin_review on subsequent verify; otherwise tier=claim_verified.
- [ ] SendGrid email sent with claim URL: `{FRONTEND_URL}/employers/claim?token={token}`
- [ ] Rate limits: 5/hour per IP, 3/hour per email (return 202 anyway when limited; log)
- [ ] `assessments_admin_router` style: registered in `backend/app/routes/__init__.py:all_routers`
- [ ] `backend/tests/test_employers_claim.py` covers: happy path domain-match, domain-mismatch routes to admin_review, rate-limit, no-enumeration (202 always for unknown listing_id), invalid email format → 422 (input shape, not enumeration), bpsai-pair arch check passes

**Depends on:** T24.2

---

### T24.4 — Listing claim verification endpoint | Cx: 20 | P0

**Description:**
`GET /api/employers/claim/verify?token=…` validates the claim token, marks it used, creates the listing_verifications row with the tier determined by T24.3's domain heuristic, sets a signed `gw_employer_account` cookie binding the browser to the employer identity. 401 uniform across invalid/expired/used; 409 cross-account-conflict (the listing was already claimed by a different employer).

**AC:**
- [ ] `backend/app/routes/employers.py` extends with `GET /api/employers/claim/verify`
- [ ] Validates token: returns uniform 401 for invalid/expired/already-used (no error oracle)
- [ ] On valid claim: marks `listing_claims.used_at`, creates `listing_verifications` (tier per domain heuristic from T24.3), sets `gw_employer_account` HMAC-signed cookie (parallel to S22 `gw_account` — separate cookie name; same HMAC pattern reusing `audit_hash_salt`)
- [ ] 409 if `listing_verifications` already exists for this listing under a different employer (UNIQUE constraint on listing_id catches it; route translates IntegrityError → 409)
- [ ] Returns `{employer_account_id, listing_id, verification_tier, next_step: "intake"}` JSON
- [ ] `backend/tests/test_employers_claim_verify.py` covers: success (claim_verified tier on domain match), success (admin_review tier on domain mismatch), 401 byte-uniform across invalid/expired/used, 409 cross-account conflict, single-use after success (replay → 401), bpsai-pair arch check passes

**Depends on:** T24.3

---

### T24.5 — Employer intake endpoint | Cx: 20 | P0

**Description:**
`POST /api/employers/{employer_account_id}/listings/{listing_id}/intake` accepts the structured intake answers (must-haves, day-1 tasks, comp band, fair-chance willingness). Gated on the `gw_employer_account` cookie matching the path's employer_account_id, OR admin role override. Pydantic-validated payload; comp_band_min ≤ comp_band_max sanity guard. Persists intake_json on the listing_verifications row + sets intake_completed_at.

**AC:**
- [ ] `backend/app/routes/employers.py` extends with `POST /api/employers/{employer_account_id}/listings/{listing_id}/intake`
- [ ] Request body: `{must_haves: list[str], nice_to_haves: list[str], real_day1_tasks: list[str], comp_band_min: int, comp_band_max: int, fair_chance_willingness: bool, additional_notes: str | None}`
- [ ] Pydantic validation: comp_band_min ≤ comp_band_max, both positive; lists non-empty for must_haves and real_day1_tasks
- [ ] Gated: requesting account holds the `gw_employer_account` cookie matching employer_account_id, OR has admin role (cookie-based via S22's `verify_account_cookie`)
- [ ] Persists intake_json + sets `intake_completed_at` on `listing_verifications`
- [ ] Returns the updated verification record (intake_json INCLUDED in response — caller is the employer who just submitted it)
- [ ] `backend/tests/test_employers_intake.py` covers: happy path, comp_band sanity guard (max < min → 422), anonymous → 403, non-owner → 403, admin override succeeds, bpsai-pair arch check passes

**Depends on:** T24.4

---

### T24.6 — Public listing fetch verification-tier extension | Cx: 15 | P0

**Description:**
Extend the existing `GET /api/jobs` response with a `verification` field per listing. intake_json EXCLUDED from public response (only `intake_complete: bool` surfaces). Anonymous-first invariant must hold — the auto-discovery test will catch drift. JOIN to listing_verifications kept O(1)-per-listing via batched read (`get_public_verification_summary` from T24.2).

`routes/jobs.py` is at 140 lines; this extension keeps it under 200.

**AC:**
- [ ] `backend/app/routes/jobs.py` extended (NOT auth.py)
- [ ] Existing `GET /api/jobs` response payload adds `verification: {tier, verified_at, intake_complete: bool} | null` per listing
- [ ] Anonymous-first invariant test passes — anonymous + claimed sessions return byte-equivalent payloads (modulo the documented account-only fields)
- [ ] `intake_json` EXCLUDED — only `intake_complete: bool` exposed; rationale documented in route docstring referencing the integrity charter
- [ ] JOIN uses `get_public_verification_summary(listing_ids)` — single batched query, not N+1
- [ ] Sets `Cache-Control: public, max-age=60` on the response (mirrors S23 public fetch)
- [ ] `backend/tests/test_jobs_verification_tier.py` covers: unverified listing returns `verification: null`, source_trust tier returns the field, claim_verified returns intake_complete=true after intake submitted, intake_json NOT leaked, anon-vs-claimed equivalence
- [ ] `bpsai-pair arch check backend/app/routes/jobs.py` passes

**Depends on:** T24.2

---

### T24.7 — Reputation event recording API | Cx: 15 | P0

**Description:**
`POST /api/listings/{listing_id}/events {kind, session_id?, notes?}` records a reputation signal. Gated by `any_of_roles("case_manager", "admin")` — case managers record placements they witness; admins record manual events. Anonymous session_id permitted in the payload so events tied to anonymous candidates aren't lost. Persists to listing_reputation_events with recorded_by = requesting account.

Lands in NEW route module.

**AC:**
- [ ] `backend/app/routes/listing_reputation.py` (new) exposes `POST /api/listings/{listing_id}/events`
- [ ] Request body: `{kind: str, session_id: str | None, notes: str | None}`; `kind` validated against `EVENT_KINDS` tuple
- [ ] Gated: `any_of_roles("case_manager", "admin")`
- [ ] Stores in `listing_reputation_events`; `recorded_by` = requesting account
- [ ] 404 if listing_id not found in `job_listings`
- [ ] Router registered in `backend/app/routes/__init__.py:all_routers`
- [ ] Listed in `backend/tests/_audit_integrity_fixtures.py` AUDIT_ALLOWLIST + `_cross_session_fixtures.py` PUBLIC_ENDPOINTS allowlists
- [ ] `backend/tests/test_listing_reputation.py` covers: each event_kind, role gating (case_manager OK, admin OK, sme_reviewer 403, anonymous 403), unknown listing 404, invalid kind 422, anonymous session_id payload supported (event records it; recorded_by still required)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T24.2

---

### T24.8 — Reputation score computation | Cx: 15 | P1

**Description:**
Implement `get_signal_rates(listing_id, window_days=30)` returning `{response_rate, withdrawal_rate, placement_rate, sample_size}`. Rolling 30-day window, computed on demand from `listing_reputation_events` (no denormalization yet — keep the schema simple; a future sprint can materialize a rolling window if perf demands).

The only P1 task this sprint — substrate works without computed rates; this is read-side ergonomics. **Cuttable scope.**

**AC:**
- [ ] `queries_listings_reputation.get_signal_rates(session, listing_id, window_days=30) -> dict`
- [ ] Returns `{response_rate: float, withdrawal_rate: float, placement_rate: float, sample_size: int, window_days: int}`
- [ ] Sample size returned so callers can hide rates when n < 5 (small-sample suppression)
- [ ] Rates computed as count_kind / sample_size
- [ ] Time window respected (events older than window_days excluded)
- [ ] `backend/tests/test_listing_reputation_rates.py` covers: empty events → all rates 0.0 sample_size 0; mixed events → correct rates; events outside window excluded; small sample (n=2) returns rates but caller should suppress per the contract; large sample correctness across kinds
- [ ] `bpsai-pair arch check` passes

**Depends on:** T24.7

---

## Phase 3: Frontend dashboard + integration

### T24.9 — Admin claim-review dashboard | Cx: 25 | P0

**Description:**
Two pages under `/admin/listings`: list of pending claims that landed in admin_review tier (domain mismatch from T24.3), and a detail page showing claim email + listing details + employer_account candidate + intake (if filled) + approve/reject buttons. Approve transitions verification_tier to admin_reviewed and creates the verification record; reject deletes the claim. Wrapped in `<RoleGate roles={["admin"]}>` from S23.

**AC:**
- [ ] `frontend/src/app/admin/listings/page.tsx` — list page; fetches via `listPendingClaims()`; filter by source/age; row click → detail
- [ ] `frontend/src/app/admin/listings/[claimId]/page.tsx` — detail; shows claim email, listing details, employer candidate, intake (if filled), approve/reject buttons
- [ ] `frontend/src/lib/api/listing_claims.ts` — typed: `listPendingClaims()`, `getClaim(claimId)`, `approveClaim(claimId)`, `rejectClaim(claimId)`. AssessmentsApiError-style typed errors
- [ ] Both pages wrapped via the existing admin layout's `<RoleGate roles={["admin","case_manager","sme_reviewer","dao_reviewer"]}>` (S23's wrap stays — gating is a strict admin-only check at the page level via `useAccountRoles().includes("admin")`)
- [ ] Approve calls `POST /api/employers/claims/{claim_id}/approve` (admin-gated; new route added to `backend/app/routes/employers.py` for this flow); reject calls `DELETE /api/employers/claims/{claim_id}` (admin-gated)
- [ ] Backend routes for approve/reject also gated by `require_role("admin")`
- [ ] Styling matches GoWork palette: approve cyan (bg-primary), reject rose (bg-destructive)
- [ ] vitest coverage: list rendering + filters, detail rendering + approve/reject submission, API client (request/response shapes + error states)
- [ ] `npx tsc --noEmit` clean; `npx next build` green

**Depends on:** T24.5

---

### T24.10 — Frontend "Verified Listing" badge component + integration | Cx: 15 | P0

**Description:**
`<VerifiedBadge tier={...} intakeComplete={...} />` renders three variants: source_trust (paler cyan, "Source Verified"), claim_verified ("Verified Employer"), admin_reviewed (same visual as claim_verified). intake_complete=true adds a "+ Intake Complete" sub-badge in amber. null/missing renders nothing. Integrate into the existing `/jobs` list page and detail page.

Charter integrity: badge is display-only. Integration gate (T24.11) explicitly tests that `backend/app/modules/matching/` reads zero verification signals.

**AC:**
- [ ] `frontend/src/components/jobs/VerifiedBadge.tsx` (new):
  - [ ] Props: `{tier: "source_trust" | "claim_verified" | "admin_reviewed" | null, intakeComplete: boolean}`
  - [ ] Three tier variants with correct palette tokens (bg-primary for verified, bg-warning for intake-complete sub-badge)
  - [ ] Tooltip per variant explaining what the tier means
  - [ ] null → renders nothing (returns null; not even a hidden div)
- [ ] Integrated into `frontend/src/app/jobs/page.tsx` (existing job list)
- [ ] Integrated into `frontend/src/app/jobs/[jobId]/page.tsx` (existing job detail page IF it exists; otherwise skip)
- [ ] vitest coverage: each tier renders correct text/style; intake_complete sub-badge appears only when true; null tier renders nothing; tooltip text per variant
- [ ] `npx tsc --noEmit` clean; `npx next build` green

**Depends on:** T24.6

---

## Phase 4: Integration gate

### T24.11 — Sprint 24 integration gate | Cx: 10 | P0

**Description:**
Final gate. Drives the full chain (claim → verify → intake → public fetch → reputation event) through HTTPX `AsyncClient` over `ASGITransport`. Mocks SendGrid at the boundary. Asserts the load-bearing charter integrity invariant: the matching engine reads ZERO verification signals.

**AC:**
- [ ] Full backend test suite green on sqlite + postgres (T23.9 isolation handles identity-layer tests on the postgres axis)
- [ ] Frontend vitest green
- [ ] `ruff check .` clean on touched files
- [ ] `bpsai-pair arch check .` no new violations
- [ ] **`auth.py` line count: 314 (UNCHANGED from sprint entry — sprint invariant)**
- [ ] `tsc --noEmit` 0 errors; `next build` green
- [ ] `backend/tests/test_listing_verification_e2e.py` (new) drives:
  1. Anonymous user does not see a verification badge → `GET /api/jobs` for a draft listing returns `verification: null`
  2. POST `/api/employers/claim {listing_id, claimant_email}` → 202 (mock SendGrid)
  3. Extract token from mocked email; GET `/api/employers/claim/verify?token=…` → 200 (claim_verified tier when domain matches)
  4. POST `/api/employers/{eid}/listings/{lid}/intake` → 200 with intake stored
  5. GET `/api/jobs` again → verification field surfaces (tier + intake_complete=true), intake_json NOT in response
  6. POST `/api/listings/{listing_id}/events {kind: response_received}` → 200 (case_manager-gated mock account)
  7. **CHARTER INTEGRITY ASSERTION:** grep `backend/app/modules/matching/` for any reference to `listing_verifications` / `verification_tier` / `intake_complete` / `listing_reputation_events` — must return zero matches. Either inline grep at test time (subprocess) or a pre-curated test file that documents the matching-engine import surface and asserts none of the new tables are imported.
- [ ] `.paircoder/context/state.md` reconciled: Sprint 24 complete entry; Current Focus updated
- [ ] PR pushed; CI green on both engine matrix axes

**Depends on:** T24.6, T24.8, T24.9, T24.10

---

## Delivery Summary

| Phase | Tasks | Cx | Output |
|---|---|---|---|
| 1. Foundation — schema + CRUD | T24.1, T24.2 | 50 | 4 new tables, 3 CRUD modules with state-machine guards |
| 2. Backend pipeline — claim/verify/intake/public/reputation | T24.3, T24.4, T24.5, T24.6, T24.7, T24.8 | 105 | Magic-link-style claim flow, intake form, public verification surface, reputation event stream + rate computation |
| 3. Frontend dashboard + badge | T24.9, T24.10 | 40 | Admin claim-review queue, `<VerifiedBadge />` integrated into `/jobs` |
| 4. Integration gate | T24.11 | 10 | E2E smoke + charter-integrity test (matching engine reads zero verification signals) |
| **Total** | **11** | **205** | Two-sided listing verification substrate ready for S25/S26 to read reputation rates |

## Priority Order

Engage cut-list (in order P2 → P1 → P0; cut from the top if budget overflows):

1. **P0 (cannot cut — load-bearing chain):** T24.1, T24.2, T24.3, T24.4, T24.5, T24.6, T24.7, T24.9, T24.10, T24.11
2. **P1 (cuttable — read-side ergonomics):** T24.8 — reputation rate computation. Substrate works without it; rate-computation can ship in a follow-up sprint when content (S26 gamification) actually needs to display rates. The event-stream itself (T24.7) is the load-bearing data capture.
3. **P2 (none):** This sprint has no cuttable scope beyond T24.8.

If budget pressure surfaces, T24.8 is the only descope. Everything else is the load-bearing pipeline chain.
