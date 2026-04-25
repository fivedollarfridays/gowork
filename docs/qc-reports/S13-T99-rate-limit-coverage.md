# T13.99 — Rate-Limit Coverage Audit

**Sprint:** S13
**Method:** Inventory every mutating endpoint; cross-check against rate-limiter call sites.
**Generated:** 2026-04-25
**Cross-reference:** T13.60 (rate limiter race + boundary tests)

## Inventory

`grep` for `@router.{post,put,patch,delete}` across `backend/app/routes/` returned **32 mutating endpoints across 17 files**.

### Files WITH rate limiters (6 files)

| File | Limit | Notes |
|------|-------|-------|
| `routes/assessment.py` | 10/60s | Per-IP rate limiter on assessment creation |
| `routes/plan.py` | 5/60s | Tighter — plan generation is LLM-expensive |
| `routes/feedback.py` | 20/60s | Lighter — feedback submissions |
| `routes/admin_flags.py` | uses `_check_rate_limit` from common helper | Per-actor (admin-key-derived hash) |
| `routes/compliance.py` | uses `_enforce_rate_limit` | Per-session limit on export/delete |
| `routes/jobs.py` | 60/60s (list endpoint only) | List read; no mutating limit |

### Files WITHOUT explicit rate limiters (11 files, 32-6=26 mutating endpoints)

| File | Endpoints | Risk class | Severity |
|------|-----------|-----------|---------|
| `routes/sendgrid_webhook.py` | 1 (POST events) | Inbound webhook; signature-verified (ECDSA) | Clean — signature gates abuse |
| `routes/pathway.py` | 1+ | Worker-callable; LLM-expensive | **MED — should rate-limit** |
| `routes/documents.py` | 5 (resume/cover-letter generation, downloads) | LLM-expensive paths | **HIGH — LLM cost** |
| `routes/simulate.py` | 1+ | Cliff simulation; CPU-bound | MED |
| `routes/appointments.py` | 4+ (create/update/cancel) | Per-session DB writes | LOW (single-row inserts) |
| `routes/share.py` | 1+ (share-link creation) | Token-shaped output | MED — could be abused for token enumeration |
| `routes/advisor_inbox.py` | 1+ (send-note) | Advisor-authenticated | LOW — gated by advisor token |
| `routes/credit.py` | 1+ | Outbound to credit microservice | **HIGH — outbound API cost** |
| `routes/demo.py` | 1+ | Dev-only? Verify | LOW (likely local-only) |
| `routes/engagement.py` | 4+ (preferences, send-now, unsubscribe GET+POST) | Per-session preference updates; admin send-now | MED |
| `routes/jobs_applications.py` | 4+ (CRUD) | Per-session writes | LOW |
| `routes/brightdata.py` | 1+ | Admin/scheduled crawl trigger | LOW (admin-gated) |

## Findings

### HIGH — Documents endpoints (5) lack rate limit

- **Site:** `routes/documents.py` POST routes for resume + cover letter generation
- **Issue:** these endpoints invoke the LLM (when `ENABLE_AI_GENERATION=true`). Without a per-session rate limit, a worker could trigger many expensive LLM calls per minute.
- **Severity:** HIGH for cost (LLM provider bills); MED for abuse (a single worker burst would also degrade service for others)
- **Fix:** add `RateLimiter(max_requests=5, window_seconds=60)` per session. Mirror the pattern in `plan.py`.

### HIGH — Credit endpoint lacks rate limit

- **Site:** `routes/credit.py` — calls outbound credit microservice
- **Issue:** outbound API per request → cost + dependency rate-limit consumed
- **Severity:** HIGH — same logic as documents
- **Fix:** add per-session rate limit; document the credit-API's own limits in the runbook

### MED — Pathway endpoint lacks rate limit

- **Site:** `routes/pathway.py`
- **Issue:** LLM-expensive simulation
- **Fix:** add per-session limit

### MED — Share-link creation lacks rate limit

- **Site:** `routes/share.py` — POST share creation
- **Issue:** unbounded share-link creation per session could be used to enumerate tokens or fill share-token table
- **Fix:** small per-session limit (5-10/hour seems generous)

### MED — Engagement send-now endpoint

- **Site:** `routes/engagement.py` — admin `/send-now` is admin-gated, but the per-session preferences route is worker-callable and not rate-limited
- **Fix:** add modest limit on `POST /preferences`

### LOW — Appointments/jobs_applications/demo/advisor

- These are session-scoped DB inserts with no expensive backend dep. Unbounded burst would just create lots of rows per session — the storage cost is minimal and bounded by `right-to-delete` (T12.36).
- Acceptable for hackathon; track for prod.

### Verified clean

- `sendgrid_webhook.py` — ECDSA signature gates abuse
- `assessment.py`, `plan.py`, `feedback.py`, `jobs.py` (list), `admin_flags.py`, `compliance.py` — all have appropriate limiters

## Summary table

| Severity | Count |
|----------|-------|
| HIGH | 2 (documents, credit) |
| MED | 3 (pathway, share, engagement preferences) |
| LOW | 5 (appointments, jobs_applications, demo, advisor, brightdata) |
| Clean | 6 files |

## Recommendation

For hackathon submission, address the **2 HIGH findings** (documents + credit) by adding rate limiters mirroring `plan.py`'s pattern. ~5 lines per file. The MED findings can ship with documented risk; LOW are acceptable.

## Out of scope

- Distributed rate limiting (single-node app; in-memory limiter is fine for current scale)
- IP-based limits (token-based / session-based is the appropriate axis here)
- Sliding-window precision (T13.60 verified the in-memory limiter is correct)
