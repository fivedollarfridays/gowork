# T13.88 — API TTFB / Latency Profile

**Sprint:** S13
**Generated:** 2026-04-25
**Harness:** `backend/tests/perf_test_api_ttfb.py`
**Machine:** darwin / Python 3.14.3
**Endpoints profiled:** 34
**Endpoints skipped:** 36
**Endpoints failing budget:** 0

## Methodology

- **Tool:** `httpx`-based `fastapi.testclient.TestClient`, in-process — no network jitter.
- **N:** 20 measured requests per endpoint (after 3 warmup calls).
- **Timer:** `time.perf_counter()` around each `client.request(...)` call.
- **Payload:** representative — for session-owned routes, a single seeded session+token; for body-required routes, the same `REQUIRED_FIELD_PLACEHOLDERS` table T13.63 uses.
- **DB:** ephemeral SQLite (per-module tmp dir) with all m001-m003 migrations applied.
- **Budgets:** read (GET) p95 ≤ 500ms, write (non-GET) p95 ≤ 2000ms.
- **Categories used:** read = GET; write = POST/PUT/PATCH/DELETE.

Status codes are printed for context — the harness does NOT
filter on status. A 4xx is a real handler exit (auth check,
404, etc.) and its TTFB is still the time to first byte.

## Per-endpoint results

| Method | Path                                                    |     p50 |     p95 |     p99 |     min |     max | Budget | Stat  | HTTP |
|--------|---------------------------------------------------------|---------|---------|---------|---------|---------|--------|-------|------|
| GET    | /api/engagement/preview-digest                          |     3.7 |     3.8 |     3.8 |     3.6 |     3.8 |  500ms | PASS  | 200 |
| POST   | /api/pathway                                            |     1.8 |     1.9 |     1.9 |     1.8 |     1.9 | 2000ms | PASS  | 200 |
| GET    | /api/plan/{session_id}/intelligence                     |     1.8 |     1.9 |     1.9 |     1.8 |     1.9 |  500ms | PASS  | 200 |
| POST   | /api/engagement/preferences                             |     1.5 |     1.7 |     2.0 |     1.4 |     2.0 | 2000ms | PASS  | 200 |
| POST   | /api/job-applications                                   |     1.5 |     1.6 |     1.6 |     1.4 |     1.6 | 2000ms | PASS  | 201 |
| POST   | /api/appointments                                       |     1.4 |     1.5 |     1.5 |     1.4 |     1.5 | 2000ms | PASS  | 201 |
| GET    | /api/intelligence/barriers                              |     1.4 |     1.5 |     1.6 |     1.4 |     1.6 |  500ms | PASS  | 200 |
| PATCH  | /api/plan/{session_id}/actions                          |     1.3 |     1.4 |     1.4 |     1.3 |     1.4 | 2000ms | PASS  | 200 |
| POST   | /api/feedback/resource                                  |     1.3 |     1.4 |     1.4 |     0.8 |     1.4 | 2000ms | PASS  | 429 |
| POST   | /api/appointments/from-pathway                          |     1.3 |     1.3 |     1.3 |     1.3 |     1.3 | 2000ms | PASS  | 200 |
| GET    | /api/insights/{session_id}                              |     1.3 |     1.3 |     1.3 |     1.2 |     1.3 |  500ms | PASS  | 200 |
| GET    | /api/documents/versions                                 |     1.2 |     1.2 |     1.3 |     1.1 |     1.3 |  500ms | PASS  | 200 |
| POST   | /api/simulate                                           |     1.2 |     1.2 |     1.2 |     1.2 |     1.2 | 2000ms | PASS  | 200 |
| GET    | /api/jobs/                                              |     1.2 |     1.2 |     1.2 |     1.2 |     1.2 |  500ms | PASS  | 200 |
| GET    | /api/engagement/events                                  |     1.2 |     1.2 |     1.2 |     1.1 |     1.2 |  500ms | PASS  | 200 |
| GET    | /api/job-applications                                   |     1.1 |     1.2 |     1.3 |     1.1 |     1.3 |  500ms | PASS  | 200 |
| GET    | /api/job-applications/funnel                            |     1.1 |     1.2 |     1.3 |     1.1 |     1.3 |  500ms | PASS  | 200 |
| GET    | /api/appointments                                       |     1.1 |     1.2 |     1.2 |     1.1 |     1.2 |  500ms | PASS  | 200 |
| GET    | /api/plan/{session_id}/sequence                         |     1.1 |     1.2 |     1.2 |     1.1 |     1.2 |  500ms | PASS  | 200 |
| GET    | /api/plan/{session_id}                                  |     1.1 |     1.2 |     1.2 |     1.1 |     1.2 |  500ms | PASS  | 200 |
| GET    | /api/appointments/upcoming                              |     1.1 |     1.1 |     1.2 |     1.1 |     1.2 |  500ms | PASS  | 200 |
| POST   | /api/plan/{session_id}/share                            |     0.7 |     1.1 |     1.1 |     0.7 |     1.1 | 2000ms | PASS  | 429 |
| GET    | /api/plan/{session_id}/career-center                    |     1.1 |     1.1 |     1.1 |     1.1 |     1.1 |  500ms | PASS  | 404 |
| POST   | /api/plan/{session_id}/refresh                          |     0.7 |     1.1 |     1.2 |     0.7 |     1.2 | 2000ms | PASS  | 429 |
| POST   | /api/compliance/export                                  |     1.0 |     1.1 |    24.7 |     1.0 |    24.7 | 2000ms | PASS  | 429 |
| POST   | /api/compliance/delete/selective                        |     1.0 |     1.1 |     1.1 |     1.0 |     1.1 | 2000ms | PASS  | 429 |
| GET    | /api/dashboard/stats                                    |     0.9 |     1.0 |     1.1 |     0.9 |     1.1 |  500ms | PASS  | 200 |
| POST   | /api/compliance/delete                                  |     1.0 |     1.0 |     1.0 |     1.0 |     1.0 | 2000ms | PASS  | 401 |
| GET    | /api/outcomes/aggregate                                 |     0.9 |     1.0 |     1.0 |     0.9 |     1.0 |  500ms | PASS  | 200 |
| GET    | /health                                                 |     0.8 |     0.9 |     1.0 |     0.8 |     1.0 |  500ms | PASS  | 200 |
| GET    | /health/ready                                           |     0.8 |     0.9 |     0.9 |     0.8 |     0.9 |  500ms | PASS  | 503 |
| GET    | /                                                       |     0.7 |     0.7 |     0.7 |     0.6 |     0.7 |  500ms | PASS  | 200 |
| GET    | /health/live                                            |     0.6 |     0.7 |     0.7 |     0.6 |     0.7 |  500ms | PASS  | 200 |
| GET    | /api/city                                               |     0.6 |     0.6 |     0.7 |     0.6 |     0.7 |  500ms | PASS  | 200 |

## Findings

No endpoint exceeds its in-process budget. Real-world
(cross-region network) latency will add ~50-200ms per call;
see Caveats.

## Top 5 slowest endpoints by p95

| Rank | Method | Path | p95 (ms) | Budget | Status |
|------|--------|------|----------|--------|--------|
| 1 | GET | `/api/engagement/preview-digest` | 3.8 | 500ms | PASS |
| 2 | POST | `/api/pathway` | 1.9 | 2000ms | PASS |
| 3 | GET | `/api/plan/{session_id}/intelligence` | 1.9 | 500ms | PASS |
| 4 | POST | `/api/engagement/preferences` | 1.7 | 2000ms | PASS |
| 5 | POST | `/api/job-applications` | 1.6 | 2000ms | PASS |

## Skipped endpoints

**Count:** 36

| Method | Path | Reason |
|--------|------|--------|
| POST | `/api/admin/flags/{name}` | Admin-key gated; different trust boundary |
| GET | `/api/advisor/sessions/{session_id}` | Advisor auth; different trust boundary |
| POST | `/api/advisor/sessions/{session_id}/note` | Advisor auth; different trust boundary |
| GET | `/api/advisor/stalled-sessions` | Advisor auth; different trust boundary |
| GET | `/api/appointments/manage` | Signed-token auth; requires single-use token mint |
| DELETE | `/api/appointments/{appointment_id}` | Path-id requires seeded appointment row |
| GET | `/api/appointments/{appointment_id}` | Path-id requires seeded appointment row |
| PATCH | `/api/appointments/{appointment_id}` | Path-id requires seeded appointment row |
| POST | `/api/appointments/{appointment_id}/attended` | Path-id requires seeded appointment row |
| POST | `/api/appointments/{appointment_id}/missed` | Path-id requires seeded appointment row |
| POST | `/api/assessment/` | Creates a new session; mutates global state — separate harness |
| POST | `/api/barrier-intel/chat` | LLM-backed (Anthropic); upstream-dominated |
| POST | `/api/barrier-intel/reindex` | Admin-key gated reindex; not session-scoped |
| POST | `/api/brightdata/crawl` | External (BrightData); upstream-dominated |
| POST | `/api/brightdata/precrawl` | External (BrightData); upstream-dominated |
| GET | `/api/brightdata/status/{snapshot_id}` | External (BrightData); upstream-dominated |
| GET | `/api/compliance/export/download` | Single-use signed download token; mint required |
| POST | `/api/credit/assess` | Anonymous self-assessment; profiled separately if needed |
| POST | `/api/demo/seed` | Admin-only demo bootstrap |
| POST | `/api/documents/cover-letter` | LLM-backed (Anthropic); upstream-dominated |
| GET | `/api/documents/cover-letter/{version_id}` | Path-id requires seeded cover-letter version row |
| GET | `/api/documents/cover-letter/{version_id}/pdf` | Path-id requires seeded cover-letter version row |
| POST | `/api/documents/resume` | LLM-backed (Anthropic); upstream-dominated |
| GET | `/api/documents/resume/{version_id}` | Path-id requires seeded resume version row |
| GET | `/api/documents/resume/{version_id}/pdf` | Path-id requires seeded resume version row |
| POST | `/api/engagement/send-now` | Admin-key gated; not session-scoped |
| GET | `/api/engagement/unsubscribe` | Signed-token auth; not session-scoped |
| POST | `/api/engagement/unsubscribe` | Signed-token auth; not session-scoped |
| GET | `/api/feedback/validate/{token}` | Token-only auth (no session_id); covered by T13.63 |
| POST | `/api/feedback/visit` | Token-only auth (no session_id); covered by T13.63 |
| GET | `/api/job-applications/community-funnel` | Token-only resolves city; profiled if added to harness |
| PATCH | `/api/job-applications/{application_id}` | Path-id requires seeded application row |
| GET | `/api/jobs/{job_id}` | Path-id requires seeded job row |
| GET | `/api/plan/shared/{share_token}` | Signed-token auth; requires single-use token mint |
| POST | `/api/plan/{session_id}/generate` | LLM-backed (Anthropic); upstream-dominated |
| POST | `/api/webhooks/sendgrid/events` | Webhook; signature-verified, not user-facing |

## Caveats

- **In-process bias.** `TestClient` runs the FastAPI app in-process via ASGI; there is no socket, no kernel TCP stack,
  no TLS handshake. Real HTTP from a remote client adds roughly 50-200ms per request (cross-region) plus TLS setup
  on cold connections. Real-world budgets should subtract that overhead from the local measurements before declaring health.
- **Cold-start.** The first request after process boot pays for
  module imports, lazy LLM-client init, and (where wired)
  sentence-transformers model load. The harness fires 3 warmup calls per endpoint before measuring
  to absorb that cost; the warmups are NOT in the percentiles.
- **SQLite write contention.** Single-writer locking causes
  occasional outliers under burst write load. With N=20, p99 is
  the worst single sample — useful as a tail indicator but not
  a tight bound. A larger N (200+) would be needed for stable p99.
- **No real network.** If a route's real bottleneck is an
  outbound call (Anthropic, SendGrid, BrightData, OpenAI), this
  harness will UNDERSTATE its latency. Those routes are skipped
  here and tracked separately.

## Recommendations

All profiled endpoints are within budget on the in-process harness. Recommendations focus on the worst-tail slice:

1. **GET /api/engagement/preview-digest** — p95 4ms (budget 500ms). Within budget but at the top of the list — keep an eye on it as feature scope grows. Investigate handler — DB query plan or sync I/O on async route.
2. **POST /api/pathway** — p95 2ms (budget 2000ms). Within budget but at the top of the list — keep an eye on it as feature scope grows. Investigate handler — DB query plan or sync I/O on async route.
3. **GET /api/plan/{session_id}/intelligence** — p95 2ms (budget 500ms). Within budget but at the top of the list — keep an eye on it as feature scope grows. Investigate handler — DB query plan or sync I/O on async route.

**Cross-cutting:**

- Ensure async routes don't fall back to sync I/O (sqlite3 inside an async handler will block the event loop).
- Add request-scoped query counters in dev to spot N+1 patterns before they hit the perf budget.
- For LLM-backed routes, consider a 'preview cached' fast path that returns the last good output while a background job refreshes — keeps the user-facing TTFB low.
- Re-run this harness after any router refactor; commit the new report alongside the change.

