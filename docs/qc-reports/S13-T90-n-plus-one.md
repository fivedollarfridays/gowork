# T13.90 — N+1 Query Audit

**Sprint:** S13
**Method:** Wrap `sqlite3.connect` with a query-count harness, replay every
worker-facing list endpoint at N=1, N=10, N=50 seeded rows. Endpoints whose
SELECT count grew linearly with response size were classified as N+1 and
fixed at the persistence layer with batched `WHERE id IN (...)` queries.
**Generated:** 2026-04-25
**Cross-reference:** T12.31 (advisor inbox), T12.18 (stall detector),
T12.13 (job applications), T12.17 (documents)

## Harness

`backend/tests/_query_counter.py` monkey-patches `sqlite3.connect` so every
connection installs a `set_trace_callback` that records each statement to
a per-block counter. Pure infrastructure noise (`PRAGMA foreign_keys`,
`BEGIN`, `COMMIT`, `ROLLBACK`) is filtered. Smoke pinned in
`backend/tests/test_query_counter_harness.py`.

The audit itself lives in `backend/tests/test_n_plus_one_audit.py`. Each
endpoint is exercised three times (N=1, 10, 50) so the per-row growth
profile is visible.

## Per-endpoint query counts

| Method | Path | N=1 | N=10 | N=50 | Pattern | Status |
|--------|------|-----|------|------|---------|--------|
| GET | `/api/job-applications` | 2 | 2 | 2 | constant | clean |
| GET | `/api/documents/versions` | 2 | 2 | 2 | constant | clean |
| GET | `/api/advisor/stalled-sessions` (pre-fix) | 7 | 52 | 252 | linear (N+1) | FIXED |
| GET | `/api/advisor/stalled-sessions` (post-fix) | 6 | 6 | 6 | constant | clean |

Counts reflect SELECT statements only (PRAGMA + BEGIN/COMMIT noise excluded).
Token-validation accounts for 1 SELECT in every endpoint; the other SELECT
in the jobs/documents lists is the hydration query.

## Findings

### F1 (HIGH) — `/api/advisor/stalled-sessions` was N+1 at the per-session stall computation

- **Trigger:** `app.modules.advisor.repository.list_stalled_sessions_for_city`
  iterated city-scoped session IDs and called
  `app.modules.engagement.stall_detector.compute_stall_for_session(sid)` per
  row. Each call issued ~5 SELECTs (sessions row, outcomes, appointments,
  applications-by-status, applications-by-session) — so a 50-row response
  cost 7 city-scope SELECTs + 50 × 5 = 257 → measured at 252 in test.
- **Symptom:** measured query count grew linearly with the response size:
  N=1 → 7, N=10 → 52, N=50 → 252. Indistinguishable from the textbook N+1
  signature.
- **Fix:** new helper `app.modules.engagement._batch_stalls.batch_compute_stalls`
  loads every signal stream in O(1) batched queries (one `WHERE session_id
  IN (...)` per stream) and runs the same pure classifier helpers
  (`classification.latest_per_barrier`, `build_barrier_stalls`,
  `classify_days`) in Python.
- **Wiring:** `list_stalled_sessions_for_city` now calls
  `batch_compute_stalls` instead of looping over `compute_stall_for_session`.
  Other callers of `compute_stall_for_session` (single-session detail, the
  nightly orchestrator's per-session scan) keep the per-session
  implementation — their query budget is already constant relative to the
  response shape they own.
- **Verification:**
  - `tests/test_batch_stalls.py` — 8 parity tests asserting the two paths
    produce identical `(days_stalled, stall_level)` tuples for: no-signal,
    session-wide MEDIUM, session-wide HARD, per-barrier, auto-advance noise
    (must NOT reset days_stalled), filed application, and a multi-session
    batch call.
  - `tests/test_n_plus_one_audit.py::test_advisor_inbox_*` — query budget
    pinned at ≤12 SELECTs for N=1, 10, AND 50. A regression that
    re-introduces a per-row lookup fails this test loudly.
  - All 12 existing `test_advisor_inbox.py` tests still pass — semantics
    unchanged, only the query plan changed.

### Verified clean

- **`/api/job-applications` GET (T12.13).** `applications.list_by_session`
  goes through `persistence.select_by_session` which is one SELECT regardless
  of result size. Pinned at 2 SELECTs (token + list).
- **`/api/documents/versions` GET (T12.17).** `_versions_db.list_versions`
  is one SELECT regardless of result size. Pinned at 2 SELECTs.
- **`/api/dashboard/stats` (read-only).** Single `SELECT barriers FROM
  sessions` aggregate. Inspection-only — no seeding harness because the
  endpoint accepts no inputs that vary the query plan.
- **`/api/appointments` GET (T12.10).** `scheduler.list_by_session` is one
  SELECT regardless of size. Inspection-only — same persistence shape as
  jobs, so the audit-harness exercise was redundant.

## Recommendations (deferred)

- **`compute_stall_for_session` itself** still issues ~5 SELECTs per call.
  That's fine for callers that legitimately scope to one session (advisor
  detail, nightly per-session scan), but if a future feature wants to scan
  N sessions outside the advisor inbox, the same N+1 shape would re-emerge
  via that path. The cleanest long-term fix would be to expose
  `batch_compute_stalls` as the canonical batch API and have
  `compute_stall_for_session` delegate to it with a single-element list.
  Out of scope for T13.90 — the current fix targets the only confirmed
  N+1 hot path.
- **SQLAlchemy async path.** The dashboard endpoints use SQLAlchemy via
  `aiosqlite`. The harness catches their statements (aiosqlite ultimately
  goes through `sqlite3.connect`), but a more idiomatic instrumentation
  would hook `sqlalchemy.event.listen("after_cursor_execute")`. Not needed
  for this audit because the SQLAlchemy callers are aggregate single-pass
  GROUP BY queries, not row-loop hydration.

## Files

**Created:**
- `backend/tests/_query_counter.py` — monkey-patch harness (contextmanager).
- `backend/tests/test_query_counter_harness.py` — 6 smoke tests.
- `backend/tests/test_n_plus_one_audit.py` — 11 audit + regression tests.
- `backend/tests/test_batch_stalls.py` — 8 parity tests vs. per-session path.
- `backend/app/modules/engagement/_batch_stalls.py` — batch classifier
  (the fix).
- `backend/app/modules/engagement/_batch_stalls_io.py` — batched SQL
  loaders (split out of `_batch_stalls.py` for arch limit).

**Modified:**
- `backend/app/modules/advisor/repository.py` — wire
  `list_stalled_sessions_for_city` to `batch_compute_stalls`. Function
  body went from 19 lines to 25 lines (added the batch call + dispatch);
  no API change.

## arch check

All new and modified files: 0 errors. Two warnings on `_batch_stalls.py`
(164L > 150L warning) and `_batch_stalls_io.py` (209L > 150L warning) —
both well under the 300L hard error and the 40-line per-function limit.
The 198L warning on `repository.py` predates this task (the diff added
6 lines).
