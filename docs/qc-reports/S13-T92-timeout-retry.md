# T13.92 — Outbound HTTP Timeout / Retry Audit

**Sprint:** S13
**Date:** 2026-04-24
**Method:** Grep `backend/app/` and `frontend/src/` for every outbound network call site (`httpx.*`, `fetch(...)`, `useQuery`, `useMutation`); classify by idempotency; verify timeout + retry behavior.
**Cross-reference:** T13.95 (SSRF surface — same call-site inventory)

## Summary

* **Backend call sites audited:** 4 (httpx) + 3 SDK-managed (Anthropic / OpenAI / Gemini / SendGrid — each handles its own retry internally; out of scope per task spec).
* **Backend clean (timeout already set):** 4/4
* **Backend retry policy fixed:** 3 GET-only call sites (BrightData snapshot poll, USAJobs, TWC) now use a shared exponential-backoff helper.
* **Frontend fetch sites audited:** 9 (4 typed-API modules + raw fetches).
* **Frontend clean (timeout already set):** 1 (`lib/api.ts` apiFetch — already had AbortController).
* **Frontend timeout added:** 7 sites.
* **react-query config:** queries `retry: 1` (acceptable); mutations default `retry: 0` (correct).

## Backend per-call-site table

| File:function | Method | Idempotent? | Timeout (s) | Retry policy | Status |
|---------------|--------|-------------|-------------|--------------|--------|
| `brightdata/client.py:trigger_crawl` | POST | NO | 30 | None — surfaces first failure | OK |
| `brightdata/client.py:trigger_keyword_crawl` | POST | NO | 30 | None — surfaces first failure | OK |
| `brightdata/client.py:get_snapshot_status` | GET | YES | 30 | **3 attempts, 0.5s/1s/2s backoff on 5xx + connect errors** | **FIXED** |
| `adapters/usajobs_adapter.py:_fetch_usajobs` | GET | YES | 15 | **3 attempts, 0.5s/1s/2s backoff** | **FIXED** |
| `adapters/adapters/twc_adapter.py:_fetch_twc_jobs` | GET | YES | 15 | **3 attempts, 0.5s/1s/2s backoff** | **FIXED** |
| `routes/credit.py:assess_credit` | POST | NO | 30 | None — surfaces first failure as HTTP 502/503/504 | OK |

### Retry helper

New module: `backend/app/integrations/_http_retry.py`
* `async_get_with_retry(client, url, **kwargs)` — exponential backoff (configurable). Used only by GET callers.
* Raises `NoRetry5xxError` after `max_attempts` consecutive 5xx; preserves the last `httpx.Response` so callers can re-extract upstream body text for diagnostics.
* Retries on `ConnectError / ReadError / ConnectTimeout / ReadTimeout` and 5xx.
* Does NOT retry 4xx — surfaces on first attempt.
* POST/PATCH/DELETE callers must NOT use this helper (enforced by convention + module docstring + test `test_brightdata_post_does_not_silently_retry_on_5xx`).

## Frontend per-fetch-site table

| File:function | uses react-query? | retry config | timeout | Status |
|---------------|-------------------|--------------|---------|--------|
| `lib/api.ts:apiFetch` | indirect (via mutations/queries) | inherits global | 30s (AbortController) | already clean |
| `lib/api.ts:streamBarrierIntelChat` | no (raw fetch + SSE) | n/a (stream) | 30s per-chunk inactivity | already clean |
| `lib/api/appointments.ts:apiFetch` | yes | inherits global | **30s (added)** | **FIXED** |
| `lib/api/jobApplications.ts:apiFetch` | yes | inherits global | **30s (added)** | **FIXED** |
| `lib/api/documents.ts:apiFetchJson/Text` | yes | inherits global | **60s (added — PDF render)** | **FIXED** |
| `lib/api/digest.ts:previewDigest` | yes | inherits global | **30s (added)** | **FIXED** |
| `lib/api/advisor.ts:advisorFetch` | yes | inherits global | **30s (added)** | **FIXED** |
| `hooks/useCityConfig.ts:fetchCityConfig` | no | n/a (singleton) | **10s (added)** | **FIXED** |
| `app/shared/[token]/page.tsx` (useEffect raw fetch) | no | n/a (one-shot) | **30s (added)** | **FIXED** |

### react-query global config

`frontend/src/lib/providers.tsx`:
```ts
new QueryClient({
  defaultOptions: { queries: { staleTime: 60_000, retry: 1 } },
})
```

* **Queries (idempotent GETs):** `retry: 1` — gentle, single retry on failure. Acceptable.
* **Mutations (POSTs):** No global override. Default react-query mutation retry is `0`. Correct — no silent double-submit.
* Two views explicitly override to `retry: 0` (case-manager + StallAlertBannerMount) — prevents banner thrash on transient errors. Reasonable.

## Out of scope (per task spec)

* **LLM SDKs (Anthropic / OpenAI / Gemini):** Each SDK has its own retry config. Not double-wrapped on our side. Not modified per task boundary.
* **SendGrid SDK:** Same — internal SDK retry; we don't wrap.
* **WeasyPrint URL fetcher:** Always rejects (`_deny_all_url_fetcher`). No outbound HTTP.

## Files modified

| File | Reason |
|------|--------|
| `backend/app/integrations/_http_retry.py` | NEW — shared retry helper for idempotent GETs. |
| `backend/app/integrations/brightdata/client.py` | `get_snapshot_status` now retries 5xx via helper; preserves upstream body text on persistent 5xx. |
| `backend/app/integrations/adapters/usajobs_adapter.py` | `_fetch_usajobs` GET wrapped with retry helper. |
| `backend/app/integrations/adapters/twc_adapter.py` | `_fetch_twc_jobs` GET wrapped with retry helper. |
| `backend/tests/test_outbound_timeout_retry.py` | NEW — 17 tests covering helper + 4 integrations. |
| `backend/tests/test_usajobs_normalize.py` | Added `mock_response.status_code = 200` to 3 tests so retry helper sees a non-Mock status. |
| `frontend/src/lib/api/appointments.ts` | Added 30s AbortController timeout. |
| `frontend/src/lib/api/jobApplications.ts` | Added 30s AbortController timeout. |
| `frontend/src/lib/api/documents.ts` | Added 60s AbortController timeout (PDF render). |
| `frontend/src/lib/api/digest.ts` | Added 30s AbortController timeout. |
| `frontend/src/lib/api/advisor.ts` | Added 30s AbortController timeout. |
| `frontend/src/hooks/useCityConfig.ts` | Added 10s AbortController timeout. |
| `frontend/src/app/shared/[token]/page.tsx` | Added 30s AbortController timeout + cleanup on unmount. |

## Verification

* `backend/tests/test_outbound_timeout_retry.py` — 17/17 pass.
* `backend/tests/test_brightdata_client.py` — 17/17 pass (regression).
* `backend/tests/test_usajobs_normalize.py` — 12/12 pass (after status_code=200 fix).
* `backend/tests/test_twc_adapter.py` — 7/7 pass.
* `backend/tests/test_credit_proxy.py` — pass (unchanged code path).
* Full backend regression: 4076 pass, 5 pre-existing failures unrelated to T13.92 (`test_batch_stalls.py` — order-dependent test pollution; `test_contract_credit_api.py` — sibling repo missing `jwt` module).
* `frontend npx vitest run` — 1109/1109 pass.
* `bpsai-pair arch check` — clean on every modified file.

## Findings

**Severity P0/P1: none.** All 4 backend call sites already had explicit timeouts before this task — the gap was retry policy on idempotent GETs, which had silently degraded to "fail closed" on first 5xx. That's the correct fail-safe direction (no double-charging, no infinite hangs) but unnecessary for read-only endpoints, where transient 502/503 from upstream edge maintenance is recoverable.

**Severity P2 (fixed):** 7 frontend raw-fetch sites had no `AbortController` timeout. Risk: a slow backend would leave React state in pending forever (no error UI, no recovery). Now bounded at 10–60s.

**Severity P3 (info):** No frontend `axios` usage found — all calls go through `fetch` or react-query. Single dependency surface.

## Recommendations

* **Tracking:** consider exporting `_http_retry.async_get_with_retry` outside `integrations/` for any future GET callers (e.g. a `routes/health` upstream probe). Today it's used by 3 adapters; the namespace is intentionally private (`_http_retry`).
* **Observability:** `_http_retry` already logs each retry attempt at WARNING level with the URL + status. For S14 dashboards, consider emitting a counter metric (`outbound_get_retry_total{integration=, status=}`) for capacity planning.
* **Future audit:** When any new HTTP integration lands, the audit guard test `test_credit_route_uses_timeout` (which inspects source for `timeout=`) is a good template — replicate per integration as a regression boundary.
