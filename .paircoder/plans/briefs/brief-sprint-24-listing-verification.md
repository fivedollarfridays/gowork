# Feature Brief: Sprint 24 — Two-Sided Listing Verification

## Idea

Stand up the **anti-fake-listing core** and the first paid revenue surface (per-verified-listing fee). Employers prove a listing is theirs via a domain-email claim flow (mirrors the S22 magic-link pattern); the verified employer fills out a structured intake (must-haves, real day-1 tasks, comp band, fair-chance willingness — the listing-side sibling of an assessment); reputation signals (response rate, withdrawal rate, placement count) are recorded as events. Public job-listing fetches surface a verification-tier badge so candidates see which listings have been claimed and stood behind.

This sprint is the **substrate**. It does NOT ship:
- The actual billing/payment integration for the per-verified-listing fee (Sprint 30 — government contract readiness includes the revenue surface formalization)
- Listing-side reputation EROSION mechanism — withdrawal-penalty UX visible to employers (S26 or S27, content-driven)
- Multi-tenant employer cohorts (Sprint 30)
- Employer self-service dashboard for managing their listings (claim + intake is enough; ongoing management can ship later)
- Domain-DNS-ownership verification (just SMTP domain match for now; deep-DNS proof deferred)

What it DOES ship: the schema, the claim flow, the intake form, the reputation event-stream, the public verification badge, and the admin queue for claims that don't auto-resolve via domain match.

## Codebase Context

- **Stack:** Python 3.11+ / FastAPI (backend), Next.js 15 / React / TypeScript / Tailwind (frontend), Postgres on Alembic (S22 substrate), shared accounts/roles infra from S22-S23.
- **Size:** ~700 source files / ~700 test files post-S23 (1:1 ratio).
- **Current sprint:** Sprint 23 (Assessment Authoring Pipeline) merged 2026-05-07 via PR #124. 8 dependabot dep bumps merged 2026-05-08.
- **Conflicting in-progress tasks:** None blocking. 5 stale (T1.7, T12.5, T12.16, T12.21, T12.24) — none touch S24 surface.
- **Existing infrastructure relied on:**
  - `accounts` / `account_sessions` / `account_roles` (S22)
  - `require_role`, `any_of_roles`, magic-link cookie pattern (S22+S23)
  - `job_listings` table (m001) — title/company/location/url/source/scraped_at/expires_at — Sprint 24 does NOT modify this table; verification metadata lives in a parallel table.
  - `employer_policies` (m001) — fair-chance + bg-check metadata keyed by employer_name. Stays untouched. Sprint 24's `employer_accounts` is a NEW concept (the verified-claim identity), not a replacement.
  - Existing ingest adapters at `backend/app/integrations/adapters/{brightdata,honestjobs,twc}_adapter.py` — these are the **source-trust** signal feed. Sprint 24 reads `job_listings.source` to assign baseline trust tier without modifying the adapters.
  - `routes/jobs.py` (140 lines) is the existing public listing surface — Sprint 24 will extend this rather than create a new public-facing fetch.

## Sprint-Level Constraints

- **`auth.py` line cap.** Currently 314 (S23 added /me roles). Hard ceiling 400. Sprint 24 must NOT extend it. Employer + listing-verification routes land in their own modules (`routes/employers.py`, `routes/listings_verification.py`, `routes/listing_reputation.py`).
- **Anonymous-first invariant for the public listing fetch.** The existing `GET /api/jobs` does not require auth. The verification-tier extension MUST keep that property — `tests/test_anonymous_first_invariant.py` will auto-discover any new public route and assert anon == claimed equivalence (modulo the documented account-only fields).
- **Charter compliance — load-bearing.** Verification tier is computed from artifacts (source-trust + claim + intake completeness + reputation events), NEVER from money. The verified badge does not unlock match position; it's display-only signal. The integrity charter principles 1–3 explicitly forbid pay-for-position and pay-for-verification.
- **Email enumeration.** Claim initiation must return 202 always (matches S22 magic-link). 401 on claim verify is uniform for invalid/expired/used.
- **No modification to `job_listings` table or ingest adapters.** Verification is parallel; `listing_verifications` carries the metadata. This avoids a S22-style migration churn during S24.
- **`employer_policies` stays as-is.** Existing matching-engine consumers (`job_matcher.py`, `criminal/queries.py`) keep using it. Future sprint can consolidate.
- **Cross-task contract edges:**
  - T24.1 (schema) → T24.2 (CRUD) → T24.3-T24.5 (claim/verify/intake) → T24.6 (public fetch extension) → T24.10 (frontend badge)
  - T24.7 (reputation events) is independent — can run in parallel with T24.6
  - T24.9 (admin claim review dashboard) consumes both T24.4 (claim-flow) and T24.5 (intake), not just one.

## Tasks

### T24.1 — Alembic migration: employer_accounts + listing_claims + listing_verifications + listing_reputation_events
- **Cx:** 25 / **Priority:** P0 / **Depends on:** none
- **Files:** `backend/alembic/versions/0014_listing_verification.py`, `backend/app/core/listings_verification_schema.py`
- **AC template:** schema
- **Custom AC:**
  - `employer_accounts(id PK, name UNIQUE, domain, verification_status, verified_at NULL, retired_at NULL, source_trust_tier, created_at)` — `domain` is the canonical email-domain match (e.g., "acmehiring.com")
  - `listing_claims(id PK, claim_token_hash UNIQUE, listing_id FK job_listings, employer_account_id FK NULL, claimant_email, claimant_account_id FK accounts NULL, expires_at, used_at NULL, created_at)` — claim token mirrors S22 magic-link pattern (SHA-256, 15-min expiry, single-use)
  - `listing_verifications(listing_id FK job_listings UNIQUE, employer_account_id FK, verification_tier, intake_completed_at NULL, intake_json TEXT NULL, verified_at, created_at)` — UNIQUE on listing_id (one verification record per listing)
  - `listing_reputation_events(id PK, listing_id FK, event_kind, session_id NULL, occurred_at, recorded_by FK accounts NULL)` — anonymous-friendly (session_id from anonymous fixtures); `event_kind` enum: `response_received | withdrawn | placed | ghosted`
  - ENUM constraints via portable CHECK clauses; tuples in schema module as single source of truth (`VERIFICATION_TIERS`, `EVENT_KINDS`, `VERIFICATION_STATUSES`)
  - SQLAlchemy Core Tables on shared `accounts_schema.metadata` so FKs resolve at create_all time (mirrors S22+S23 pattern)
  - Index on `(listing_id, occurred_at)` on listing_reputation_events for the rolling-window reputation hot path
  - alembic upgrade head clean on both engines

### T24.2 — queries_employers.py + queries_listings_verification.py CRUD modules
- **Cx:** 25 / **Priority:** P0 / **Depends on:** T24.1
- **Files:** `backend/app/core/queries_employers.py`, `backend/app/core/queries_listings_verification.py`, `backend/tests/test_queries_employers.py`, `backend/tests/test_queries_listings_verification.py`
- **AC template:** CRUD
- **Custom AC:**
  - `queries_employers`: create_employer_account, get_employer_by_domain, list_pending_admin_review
  - `queries_listings_verification`: mint_listing_claim_token, find_unused_claim_by_hash, mark_claim_used, create_verification, set_intake, get_verification_for_listing, get_public_verification_summary (excludes intake_json from public surface — intake answers are reviewer-internal until further notice)
  - `queries_listings_reputation`: record_event, get_signal_rates(listing_id, window_days=30), aggregate_for_employer
  - State-machine guards: claim must be unused + unexpired before mark_claim_used; verification can transition source_trust → claim_verified → admin_reviewed (one-way)
  - All queries portable across sqlite + postgres (text() + named binds + RETURNING id)

### T24.3 — Listing claim initiation endpoint
- **Cx:** 20 / **Priority:** P0 / **Depends on:** T24.2
- **Files:** `backend/app/routes/employers.py` (new), `backend/app/routes/__init__.py` (register router), `backend/tests/test_employers_claim.py`
- **AC template:** API endpoint
- **Custom AC:**
  - `POST /api/employers/claim {listing_id, claimant_email}` → 202 always (no enumeration)
  - Token: `secrets.token_urlsafe(32)`; SHA-256 stored in claim_token_hash
  - 15-min expiry; single-use
  - Domain heuristic: extract domain from claimant_email; lookup or auto-create employer_accounts row keyed by domain. If listing.company doesn't fuzzy-match the domain, route to admin queue (verification_tier=admin_review) instead of auto-verifying.
  - SendGrid email to claimant with claim URL (mirrors S22 magic-link)
  - Rate limited 5/hour per IP, 3/hour per email (slightly tighter than magic-link since this is employer-side)
  - Tests cover: happy path, domain match, domain mismatch → admin queue, rate-limit, no-enumeration

### T24.4 — Listing claim verification endpoint
- **Cx:** 20 / **Priority:** P0 / **Depends on:** T24.3
- **Files:** `backend/app/routes/employers.py` (extend), `backend/tests/test_employers_claim_verify.py`
- **AC template:** API endpoint
- **Custom AC:**
  - `GET /api/employers/claim/verify?token=...` → 200 success / 401 uniform (invalid/expired/used) / 409 cross-account-conflict
  - On success: marks claim used, creates listing_verifications row with verification_tier=claim_verified, sets gw_employer_account cookie (HMAC-signed parallel to S22's gw_account)
  - Returns `{employer_account_id, listing_id, verification_tier, next_step: "intake"}` so the frontend can route to the intake form
  - Tests cover: success, 401 oracle uniformity, 409 cross-account, single-use after success

### T24.5 — Employer intake endpoint
- **Cx:** 20 / **Priority:** P0 / **Depends on:** T24.4
- **Files:** `backend/app/routes/employers.py` (extend), `backend/tests/test_employers_intake.py`
- **AC template:** API endpoint
- **Custom AC:**
  - `POST /api/employers/{employer_account_id}/listings/{listing_id}/intake` accepts `{must_haves: [str], nice_to_haves: [str], real_day1_tasks: [str], comp_band_min: int, comp_band_max: int, fair_chance_willingness: bool, additional_notes: str}`
  - Gated: requesting account is the employer_account.verified_by_account_id (cookie-verified) OR has admin role
  - Pydantic validation; comp_band ranges sane (min ≤ max, both positive)
  - Persists intake_json + sets intake_completed_at on listing_verifications
  - Returns updated verification record
  - Tests cover: happy path, comp_band sanity guard, anonymous 403, non-owner 403, admin override succeeds

### T24.6 — Public listing fetch verification-tier extension
- **Cx:** 15 / **Priority:** P0 / **Depends on:** T24.2
- **Files:** `backend/app/routes/jobs.py` (extend — currently 140 lines, headroom available), `backend/tests/test_jobs_verification_tier.py`
- **AC template:** API endpoint extension
- **Custom AC:**
  - Existing `GET /api/jobs` response payload extended with `verification: {tier, verified_at, intake_complete: bool} | null` per listing
  - Anonymous-first invariant: route stays public; auto-discovery test passes (anon == claimed equivalence)
  - intake_json EXCLUDED from public response (only the `intake_complete` boolean surfaces); rationale: intake details are reviewer/employer-internal
  - JOIN to listing_verifications kept O(1)-per-listing via the existing pagination shape
  - Tests cover: unverified listing returns `verification: null`, source-trust tier listing returns tier=source_trust, claim-verified returns tier=claim_verified + intake_complete=true after intake submitted

### T24.7 — Reputation event recording API
- **Cx:** 15 / **Priority:** P0 / **Depends on:** T24.2
- **Files:** `backend/app/routes/listing_reputation.py` (new), `backend/app/routes/__init__.py` (register), `backend/tests/test_listing_reputation.py`
- **AC template:** API endpoint
- **Custom AC:**
  - `POST /api/listings/{listing_id}/events {kind: response_received|withdrawn|placed|ghosted, session_id?, notes?}`
  - Gated: any of (case_manager, admin) — case managers record placements; admins record manual events
  - Stores in listing_reputation_events; recorded_by = requesting account
  - Anonymous session_id permitted in payload (so events tied to anonymous candidates aren't lost)
  - Tests cover: each event_kind, role gating (case_manager OK, admin OK, anonymous 403), unknown listing 404

### T24.8 — Reputation score computation
- **Cx:** 15 / **Priority:** P1 / **Depends on:** T24.7
- **Files:** `backend/app/core/queries_listings_reputation.py` (extend with rate computation), `backend/tests/test_listing_reputation_rates.py`
- **AC template:** computation
- **Custom AC:**
  - `get_signal_rates(listing_id, window_days=30) -> {response_rate, withdrawal_rate, placement_rate, sample_size}`
  - Rolling 30-day window, computed on demand from listing_reputation_events (no denormalization yet — keep schema simple; a future sprint can add a materialized rolling window if perf demands)
  - sample_size returned so frontend can show "based on N events" / hide rates when sample is too small (n < 5)
  - Cuttable scope marker: this is the only P1 task in the sprint — the substrate works without computed rates; rates are surfaceable in a follow-up.

### T24.9 — Admin claim-review dashboard
- **Cx:** 25 / **Priority:** P0 / **Depends on:** T24.5
- **Files:** `frontend/src/app/admin/listings/page.tsx` (new — claim queue list), `frontend/src/app/admin/listings/[claimId]/page.tsx` (new — claim detail + approve/reject), `frontend/src/lib/api/listing_claims.ts` (new), `frontend/src/__tests__/admin/listings/`
- **AC template:** page + API client
- **Custom AC:**
  - List page: pending claims (those routed to admin_review tier from T24.3 domain mismatch); filter by source/age
  - Detail page: shows claim email, listing details, employer_account candidate, intake (if filled), approve/reject buttons
  - Approve transitions verification_tier to admin_reviewed and creates the verification record; reject deletes the claim
  - Wrapped in `<RoleGate roles={["admin"]}>` (S23 component)
  - vitest coverage for both pages + API client
  - Reuses `useAccount`/`useAccountRoles` hooks from S23

### T24.10 — Frontend "Verified Listing" badge component + integration
- **Cx:** 15 / **Priority:** P0 / **Depends on:** T24.6
- **Files:** `frontend/src/components/jobs/VerifiedBadge.tsx` (new), `frontend/src/app/jobs/page.tsx` (insertion — existing job list), `frontend/src/app/jobs/[jobId]/page.tsx` (insertion if it exists, otherwise list-only), `frontend/src/__tests__/jobs/verified-badge.test.tsx`
- **AC template:** component + integration
- **Custom AC:**
  - `<VerifiedBadge tier={...} intakeComplete={...} />` renders three variants:
    - source_trust → small badge "Source Verified" (paler cyan), tooltip explains the listing came from a known feed
    - claim_verified → "Verified Employer" badge (full cyan), tooltip explains the employer claimed and confirmed
    - admin_reviewed → same visual as claim_verified
    - null/missing → renders nothing
  - intake_complete=true adds a "+ Intake Complete" sub-badge (amber) — signals candidate-readable structured listing
  - Charter integrity: badge is display-only; matching engine reads zero verification signals (verify with grep against `backend/app/modules/matching/`)
  - vitest coverage: each tier renders correct variant; null renders empty

### T24.11 — Sprint 24 integration gate
- **Cx:** 10 / **Priority:** P0 / **Depends on:** T24.6, T24.9, T24.10, T24.8
- **Files:** `backend/tests/test_listing_verification_e2e.py` (new), `.paircoder/context/state.md` (reconcile)
- **AC template:** integration gate
- **Custom AC:**
  - Full backend test suite green on sqlite + postgres (with T23.9 isolation)
  - Frontend vitest green
  - ruff/arch/tsc/build clean
  - `auth.py` line count: still 314 (sprint invariant — don't grow it)
  - `backend/tests/test_listing_verification_e2e.py` drives:
    1. claim initiation (mock SendGrid)
    2. claim verification via token
    3. intake submission
    4. public fetch — assert verification surfaces; intake_json NOT leaked
    5. reputation event recorded
    6. assert charter invariant — matching engine reads zero verification signals (test inspects job_matcher / pvs_scorer call sites)
  - state.md reconciled: Sprint 24 complete entry
  - PR pushed; CI green on both engine matrix axes

## Dependency Graph

```
Wave 0 (entry):     T24.1
                      │
Wave 1:             T24.2
                      │
Wave 2:             T24.3 ──────┬─────────────┐
                                │             │
Wave 3:             T24.4       T24.6 ── T24.10 ──┐
                      │                            │
Wave 4:             T24.5 ──┐                      │
                            │                      │
Wave 5:                     T24.7                  │
                              │                    │
Wave 6:                     T24.8                  │
                              │   T24.9            │
Wave 7 (GATE):                T24.11 ──────────────┘
```

Reading the graph (engage will compute exact waves from `Depends on:` lines):
- T24.6 (public fetch extension), T24.7 (reputation events), and T24.10 (frontend badge) all only need T24.2 / T24.6 — they can all run in parallel after T24.2 lands. Wave 2-3 fans out; Wave 4-6 fans back in.
- T24.9 (admin dashboard) needs T24.5 to exist before it can render the intake-completed claim queue; but it can run parallel with T24.7/T24.8 once T24.5 lands.

## File Collision Matrix

| Wave | Tasks parallel | Shared files | Resolution |
|---|---|---|---|
| Wave 3-ish | T24.4, T24.6, T24.7, T24.10 | T24.4 + T24.5 both extend `routes/employers.py`. T24.6 extends `routes/jobs.py`. T24.7 creates `routes/listing_reputation.py`. T24.10 is frontend. | T24.4 + T24.5 are sequential (both touch employers.py); T24.6 / T24.7 / T24.10 disjoint. Clean. |
| Wave 5-ish | T24.8 + T24.9 | none — T24.8 backend computation, T24.9 frontend dashboard | clean |

No cross-task collisions beyond the dependency graph.

## Sprint Budget

- **Total Cx:** 205
- **Task count:** 11
- **P0 count:** 10
- **P1 count:** 1 (T24.8 reputation rate computation — substrate works without it)
- **P2 count:** 0

Cuttable scope: T24.8 only. Reputation event recording (T24.7) is the load-bearing data capture; rate computation (T24.8) is the read-side ergonomics that can wait one sprint.

## Integration Points (cross-task only)

- **T24.1 → T24.2:** schema → CRUD; standard pattern.
- **T24.2 → T24.3 / T24.4 / T24.5:** CRUD surface used by all three claim-flow endpoints.
- **T24.4 → T24.5:** verification record must exist before intake can target it.
- **T24.5 → T24.9:** admin dashboard reads the intake state to show review queue.
- **T24.6 → T24.10:** frontend badge consumes the verification field added to public job-listings response.
- **T24.7 → T24.8:** rate computation reads the events table.
- **Anonymous-first invariant test from S22 auto-discovers T24.6 extensions to /api/jobs.** Charter integrity: grep `backend/app/modules/matching/` confirms verification fields not read.
- **`gw_employer_account` cookie added by T24.4** — parallel to `gw_account` from S22 but scoped to employer identity. Single account can hold both cookies; future consolidation possible.

## Out of Scope

Explicit boundaries — these come in later sprints, not Sprint 24:

- **Per-verified-listing fee billing/payment integration** — Sprint 30 (gov contract readiness) when revenue surface formalization lands
- Listing reputation EROSION (visible employer penalty for ghost-withdrawal) — Sprint 26 or 27, content-driven
- Employer self-service dashboard for ongoing listing management — claim + intake is enough for now; ongoing edits ship later
- Multi-tenant employer cohorts — Sprint 30
- Deep DNS-ownership verification — just SMTP domain match for now
- Reputation event ingest from external integrations (e.g., scraping employer responses from job boards) — manual case-manager records only this sprint
- Migration of `employer_policies` to FK against `employer_accounts` — orthogonal cleanup; future sprint
- Vocational + DAO-tech assessment authoring (S25/S26)
- Phone-OTP / OAuth login (S25)

## Open Questions (defaults picked; revisit during engage)

1. **Domain-match heuristic strictness:** strict (only @company.com matches; anything else routes to admin queue) vs permissive (subdomain emails OK). Default: strict for now — false positives in admin queue are cheaper than false-claim-grants.
2. **Listings without a known employer domain:** what's the fallback? Default: claimable but routes to admin queue with full review.
3. **Reputation score formula:** simple per-signal rate over 30 days vs weighted by recency. Default: simple, computed on demand. Materialized rolling-window can ship in a future sprint if perf demands.
4. **`gw_employer_account` cookie vs reusing `gw_account`:** separate cookie for explicit employer-context separation, even though one account can hold both roles. Default: separate cookie, scoped to employer routes only.
5. **intake_json visibility:** publicly visible (transparency) vs reviewer-internal (privacy). Default: reviewer-internal — only `intake_complete` boolean surfaces publicly. Charter principle 4 (auditability) is satisfied by exposing the boolean + the verification tier; the structured intake answers stay internal until the integrity-charter amendment process flips it.
