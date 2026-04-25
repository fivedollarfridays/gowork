# S13-T72: Empty-Profile Page Breakage Sweep

**Sprint:** S13 Platform QC (Tier-3 exploratory)
**Date:** 2026-04-25
**Branch:** sprint/s13-platform-qc
**Probe target:** https://montgowork-staging-{api,web}.fly.dev
**Time-box:** ~35 min

## Summary

Created a fresh, minimal-data session via `POST /api/assessment/` with `barriers: {}` and `work_history: ""`, then probed every API endpoint the frontend pages call and walked the page-level code paths that would render that data. Cross-checked nothing-set fields (no resume, no credit, no record, no benefits, no appointments, no job applications, no documents) against component code to find unguarded array access, raw error leakage, or ugly empty states.

**Findings count by severity:**
- High: **0** (no crashes / 500s / blank screens found)
- Medium: **3** (visible UX defects that judges will notice)
- Low: **3** (rough edges, not breakage)
- Clean: 7 routes confirmed graceful

**API behavior is generally robust.** All session-scoped endpoints accept the empty-session UUID + `feedback_token` and return 200 with sensible empty shapes (`[]`, `null`, `0`). No KeyErrors, no 500s on any probed endpoint. Auth gates and missing-token paths return 401/422 with clean JSON.

**Frontend behavior is generally robust.** Most pages have `length > 0` gates, optional chaining, and explicit empty-state copy. The defects below are concentrated in two surfaces: the **shared plan view** (back-end always-broken issue) and a few "make it look like nothing's happening" cases on `/plan` and `/daily`.

## Top 3 most-broken pages

1. **`/shared/[token]`** — empty "Barriers" card with no badges and no fallback text; broken phone link with empty `tel:` href; `created_at` rendered raw with microseconds; `career_center_name` is just `"Montgomery"`, not a real career-center name. Backend hardcodes `career_center_phone: ""`.
2. **`/plan` ComparisonView** — renders "What Changes in 3 Months" with `0 active barriers → No barriers identified` and `0 eligible now → 0 eligible after plan completion`. Reads as a broken/empty section rather than a meaningful comparison.
3. **`/daily`** (digest) — for empty session, only renders the page title `[MontGoWork] Your daily digest — Saturday, Apr 25` plus a single "This week — coming soon" collapsible. No yesterday/today/stall sections (correctly hidden), but the page reads as nearly blank.

---

## Findings

### M-1. SharedPlanView shows broken phone link + empty barriers card on empty session
- **Route:** `/shared/[token]`
- **HTTP:** 200
- **Symptom:** Backend `/api/plan/shared/{token}` returns:
  ```json
  {
    "barriers": [],
    "next_steps": ["Montgomery Career Center, 334-286-1746, ..."],
    "career_center_name": "Montgomery",
    "career_center_phone": ""
  }
  ```
  Frontend `SharedPlanView.tsx:77-84` always renders a "Barriers" card; with empty input, `BarrierBadges` produces an empty `<div>` inside it (no fallback). At lines 102-109, an `<a href={toTelHref("")}>` renders a phone icon with no number and a `tel:` href that does nothing when clicked.
- **Backend root cause:** `backend/app/routes/share.py:128-129` hardcodes `career_center_name: get_city_config().name` (which is just "Montgomery", not "Montgomery Career Center") and `career_center_phone: ""`. This is broken for **all** sessions, not just empty ones — it just shows up most starkly on empty.
- **Suggested fix:**
  - `share.py`: use `get_career_center(state).name` and `.phone` (same helpers `/plan` uses) instead of city config + empty string.
  - `SharedPlanView.tsx`: gate `<BarrierBadges>` on `barriers.length > 0`, show "No barriers identified — focus on direct job search" otherwise. Conditionally render the phone link only when `career_center_phone` is non-empty.

### M-2. ComparisonView shows degenerate "0 → 0" rows on empty session
- **Route:** `/plan`
- **HTTP:** 200
- **Symptom:** `frontend/src/components/plan/ComparisonView.tsx:36-63` always pushes a "Barriers" row and a "Job Matches" row regardless of input. For an empty session this renders:
  - Today: "0 active" → In 3 Months: "No barriers identified"
  - Today: "0 eligible now" → In 3 Months: "0 eligible after plan completion"
  Reads as a broken before/after comparison.
- **Suggested fix:** in `buildRows`, skip the Barriers row when `activeBarriers === 0`, and skip the Job Matches row when `eligibleNow === 0 && eligibleAfter === 0`. If `rows.length === 0` after filtering, hide the whole "What Changes in 3 Months" section, or replace it with a single line: "Your assessment didn't surface specific barriers — head straight to the Career Center."

### M-3. Job Readiness "developing — 41/100" on a totally-empty session is misleading
- **Route:** `/plan`
- **HTTP:** 200
- **Symptom:** Backend always returns `job_readiness` with `overall_score: 41, readiness_band: "developing"` for a no-data session, because the score formula gives 100/100 on Barrier Resolution (no barriers to resolve) and 100/100 on Credit Readiness (no credit barrier), inflating a profile with zero work history / zero industries / zero resume to "developing". The factor breakdown then shows "Skills Match 20/100, Industry Alignment 20/100, Work Experience 0/100" alongside the "developing" badge — confusing.
- **Suggested fix (backend):** in the readiness scorer, if work_history is empty and resume_text is empty and target_industries is empty, treat the assessment as incomplete and either return `null` job_readiness or a `band: "incomplete_profile"` with a "Finish your assessment to see your readiness score" summary. Frontend already has the gate `plan.job_readiness && (...)` so a `null` would cleanly suppress the section.

### L-4. Daily digest is near-empty for empty session
- **Route:** `/daily`
- **HTTP:** 200
- **Symptom:** Backend returns digest text `"Hi friend,\n\nNothing new today — keep going.\n"` with all four `section_counts` at 0. Frontend `daily/page.tsx:100-115` correctly hides yesterday/today/stall sections. The only thing rendered is the page title, a subtitle (`"[MontGoWork] Your daily digest — Saturday, Apr 25"`), and a collapsible "This week" section showing "coming soon" italic placeholder text. Functional but not informative — judges who land here first will think the app is empty.
- **Suggested fix:** when all four counts are 0 and the digest contains the "Nothing new today" body, render a friendly empty state: "Your digest will fill in as you start using MontGoWork. [Visit your Plan →]"

### L-5. SharedPlanView renders raw ISO timestamp with microseconds
- **Route:** `/shared/[token]`
- **HTTP:** 200
- **Symptom:** `SharedPlanView.tsx:72` does `{generatedLabel} {plan.created_at}`, which prints `Generated on 2026-04-25T16:11:22.291701+00:00`. Looks like a backend leak.
- **Suggested fix:** format with `new Date(plan.created_at).toLocaleDateString()` or similar. (Note: backend returns the timestamp as-is from SQLite, including microseconds.)

### L-6. `/api/jobs/{job_id}` 422 leaks raw FastAPI validation detail
- **Route:** `/api/jobs/{job_id}` (backend)
- **HTTP:** 422
- **Symptom:** Passing a non-int (e.g., a UUID-shaped string) returns `{"detail":[{"type":"int_parsing","loc":["path","job_id"],"msg":"Input should be a valid integer..."}]}`. Frontend doesn't currently call this endpoint with invalid IDs, so this is dormant — but if anything ever does (deep-linked URL, future feature), the message could surface as `Error: ...` in a toast since `apiFetch` does `body.detail || \`API error ${res.status}\``.
- **Suggested fix:** None urgent. If a frontend caller is added, ensure the error path strips the FastAPI `detail` array and shows a generic "Job not found" instead.

---

## Clean routes (empty-session graceful)

- **`/`** — landing page, all stats are static city-config numbers; no session dependency. The pre-animation `0.0%` / `0K+` in the SSR HTML snapshot is the `AnimatedCounter` initial state, not a bug.
- **`/assess`** — wizard, the `barriers` step gates `canAdvance` on `barrierCount > 0`, so empty submission is blocked in normal UX. (The API does accept `barriers: {}` if a custom client bypasses the wizard — used to set up this sweep.)
- **`/credit`** — pure form, no session dependency.
- **`/jobs`** — empty `applications` shows `t("jobs.emptyBoard")`; `FunnelStatsSidebar` handles all-null rates with `hasAnyRate` gate showing `t("jobs.funnelNoData")`.
- **`/appointments`** — empty list shows `t("appointments.emptyList")`; calendar receives `[]` and renders cleanly. `placeholders.length > 0` gates the placeholder prompt.
- **`/documents/resume`** — empty `versions` triggers `t("documents.historyEmptyResume")` empty state in `VersionHistoryList`.
- **`/documents/cover-letters`** — empty `resumes` triggers the form's `resumeVersionEmpty` label and disables submission via `hasResume` gate.
- **`/case-manager`** — `DashboardStats` divides `total_assessments / total_assessments` with explicit `> 0` guard; `common_barriers.length > 0` gates the bar chart. Without an `?advisor_token=...`, `NeedsAttentionSection` simply doesn't render. Graceful.

---

## Out of scope / not probed

- **`/feedback/[token]`** — token-gated, requires a real backend feedback flow.
- **`/admin/qc`** — fail-closed in prod (returns 404 without `X-Admin-Key` header). Confirmed 404 on staging; not a finding.
- **Time-dependent stale-session paths** — could not exercise share-link expiry (`expires_at <= now`) or stall detection without seeding past timestamps.
- **JS-runtime-only crashes** — curl can only see SSR HTML. A dedicated Playwright run hitting `/plan?session=<empty-sid>&token=<feedback-token>` and watching the console for unhandled errors would close the loop on hydration-time exceptions; deferred as out of the 30-45 min budget.

---

## Methodology notes

1. Walked `frontend/src/app/` for all `page.tsx` files (12 routes, 2 token-gated skipped).
2. Created an empty session: `POST /api/assessment/` with minimum required fields (`zip_code: 36101, employment_status: unemployed, barriers: {}, work_history: ""`). Captured returned `session_id` and `feedback_token`.
3. Probed all 14 session-scoped backend endpoints (with `?token=`) for an empty session — all 200.
4. Probed error edges: bad UUID, bad token, nonexistent feedback token, nonexistent share token. All return clean 401/404/422.
5. Read each frontend page component plus its child components for `length`, array indexing, and date/string handling against the actual response shapes.
6. Observed the share-link end-to-end (POST share → GET shared) since shared plan is a likely judge-clicked feature.

## Suggested follow-ups

- **Sprint S13 fix:** M-1 backend share-route (5-line fix in `share.py`) — high judge-visibility, low effort.
- **Sprint S13 fix:** M-2 ComparisonView empty-row filter — small fix in `buildRows`.
- **Defer to S14:** M-3 readiness score for incomplete profiles (needs scorer redesign).
- **Defer to S14:** L-4 daily digest first-time empty state (needs UX copy).
