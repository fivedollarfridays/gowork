# S13 T13.71 — Cross-Session Data Leak Attempt

**Type:** Tier-3 exploratory adversarial sweep
**Branch:** `sprint/s13-platform-qc`
**Date:** 2026-04-24
**Tester:** Claude (Opus 4.7) under T13.71 brief
**Scope:** API-level cross-session leak attempts — IDOR, side channels, aggregation leaks, error oracles, confused-deputy patterns
**Out of scope:** browser-mediated attacks (CSRF, XSS), CLI/MCP surfaces, auth provider (Authn) rotation logic

---

## Summary

| Severity | Count |
|---|---|
| **P0** (active leak, exploitable now) | **0** |
| **P1** (information disclosure with realistic attack chain) | **1** |
| **P2** (existence/enumeration oracle, low practical exploitability) | **3** |
| **Verified clean** | 29 session-owned + 9 path-id + 5 aggregate + 6 admin/signed-token routes |

- **Endpoints catalogued:** 74 (`app.routes`).
- **Endpoints actively probed cross-session:** 29 session-flagged + every path-id resource (appointments, applications, documents) + every aggregate + share/manage/unsubscribe signed-token routes.
- **Staging unavailable** (503 / curl exit 28 throughout the sweep) — all probes were run against an in-process `TestClient` wired to a freshly migrated SQLite file with two pre-seeded sessions and tokens. T13.63's reproducer scaffolding (`tests._cross_session_fixtures`, `tests._route_inventory`) was reused as the harness. T13.63 suite still green: `6 passed`.

The cross-session enforcement story is **strong** at the route layer. Every authenticated session-owned endpoint enforces 403 on `(session-A id, session-B token)` — including the four routes that take `session_id` in the path *only* (no body), which T13.63's introspection does pick up via the path-param walker. The handler-side allowlisted path-id resources (appointments / documents / applications) all return 403 cross-session and 404 on missing rows. Compliance export/delete enforces session-token match and the field-name confusion (token vs session_token) returns 422, not a leak.

The findings below are **defense-in-depth gaps**, not breaks.

---

## Findings

### P1 — Share endpoint leaks `session_id` and full `barriers` list to any holder of the share URL

- **Endpoint:** `GET /api/plan/shared/{share_token}`
- **File:** `backend/app/routes/share.py:89-130`
- **Payload:**
  ```bash
  curl https://api.example/api/plan/shared/sharetokA
  ```
- **Observed:** 200 with body
  ```json
  {
    "session_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "created_at": "2026-04-25T16:04:07.199847+00:00",
    "barriers": ["criminal_record"],
    "next_steps": ["step1", "step2"],
    "career_center_name": "Montgomery",
    "career_center_phone": ""
  }
  ```
- **Expected:** Public share endpoint should display plan content WITHOUT the worker's persistent UUID (`session_id`) and WITHOUT the raw barrier slugs. The barrier list is the most-sensitive payload in the system (`criminal_record`, `credit`, `housing`, `health` …) and is what the entire compliance / pseudonymization rail in T13.59 (`hash_session_id`) is designed to keep out of audit dumps. The share endpoint funnels both back to the public web.
- **Realistic attack chain:**
  1. Worker forwards their `/shared/{token}` link to a trusted contact (designed flow).
  2. Email is auto-forwarded by recipient's filter, archived in shared inbox, posted to a Slack channel, indexed by an enterprise mail archiver, or simply leaked from a recipient's compromised webmail.
  3. Anyone who lands on the URL learns (a) the worker's persistent backend identifier (`session_id`) and (b) which protected categories they fall into (`criminal_record`).
  4. The `session_id` is then a bearer-equivalent identifier elsewhere — combined with leaked `feedback_token`s from any other source it would be a full takeover. On its own it lets an attacker correlate the worker across logs/audits/funnel data they may obtain via other means.
- **Severity rationale (P1, not P0):** No active session takeover happens — the share endpoint does not return the feedback token. The leak is the worker's UUID + protected-category profile, which is significant under the same threat model that drove T13.59's audit-row hashing.
- **Suggested fix:** In `get_shared_plan` strip `session_id` from the response and either (a) drop `barriers` entirely from the public payload, or (b) replace raw slugs with friendlier label strings already used in the worker UI. The handler already has `get_city_config()` and `_extract_next_steps()` — enough public surface for the share use case. If `barriers` is truly needed (e.g., for the resident summary copy), pass it server-side into a pre-rendered narrative string and only return that string. A follow-up driver task should:
  - Remove `session_id` from the response dict.
  - Replace `barriers` with a pre-rendered narrative or omit.
  - Add a regression test in `backend/tests/test_share_routes.py` asserting neither `session_id` nor recognised barrier slugs appear in the response body.

---

### P2 — Appointment-id existence oracle (403 vs 404 differentiation)

- **Endpoints:**
  - `GET /api/appointments/{appointment_id}`
  - `PATCH /api/appointments/{appointment_id}`
  - `DELETE /api/appointments/{appointment_id}`
  - `POST /api/appointments/{appointment_id}/attended`
  - `POST /api/appointments/{appointment_id}/missed`
- **File:** `backend/app/routes/_appointments_helpers.py:89-100`
- **Payload:** with any valid feedback token TOK_X for session X, iterate `appointment_id ∈ [1..N]`:
  ```bash
  curl "https://api/api/appointments/1?token=TOK_X"     # 403 if exists in another session
  curl "https://api/api/appointments/9999?token=TOK_X"  # 404 if id is unused
  ```
- **Observed:** sequential-integer appointment IDs let any caller with a single valid token enumerate the entire appointment ID space and learn which IDs are populated.
- **Expected:** A uniform 404 for both "appointment exists in another session" and "appointment does not exist" — the caller has no business distinguishing the two.
- **Severity rationale:** The leak is *count* of foreign appointments, not their content. No PII, no barrier data, no plan content is disclosed. But it breaks the cardinality/usage assumption that the rest of the demo seeds rely on for k-anonymity bounds. Combined with the funnel endpoints' k=5 suppression, it lets an attacker undermine the assumption that "you never know how many sessions exist."
- **Suggested fix:** In `load_owned_appointment` collapse the cross-session 403 and the missing-row 404 into a single `404 Not Found`. Same change in `_load_owned_version` (documents) and `_load_owned_application` (job-applications) for consistency. This is a small breaking change for any client that relies on the 403 distinction; recommend gating behind an env flag for one release and audit-logging the choice.

### P2 — Document version & job-application IDOR oracles (same shape as above)

- **Endpoints:**
  - `GET /api/documents/resume/{version_id}` and `/pdf`
  - `GET /api/documents/cover-letter/{version_id}` and `/pdf`
  - `PATCH /api/job-applications/{application_id}`
- **Files:** `backend/app/routes/documents.py:54-66`, `backend/app/routes/jobs_applications.py:102-116`
- **Observed:** Same 403-vs-404 split. Resume / cover-letter versions and applications also use sequential integer IDs.
- **Suggested fix:** Same fix as above (collapse to 404). The unit-test files (`test_documents_routes.py`, `test_jobs_applications_routes.py`) already pin the 403 — those tests would need to flip to 404 alongside the handler change.

### P2 — Feedback-token validation oracle

- **Endpoint:** `GET /api/feedback/validate/{token}`
- **File:** `backend/app/routes/feedback.py:64-72`
- **Payload:**
  ```bash
  curl "https://api/api/feedback/validate/<arbitrary-string>"
  ```
- **Observed:** `200` for a live token, `410 Token expired` for a known-but-expired token, `404 Token not found` for an unknown string.
- **Expected:** Uniform `404` (or uniform `401`) for any non-200 case. Distinguishing "expired" from "unknown" lets a caller test whether a token guess existed at any point.
- **Severity rationale (P2):** Token entropy is 96 bits (`secrets.token_urlsafe(12)`) so brute-force enumeration is computationally infeasible. The oracle only matters in scenarios where an attacker has obtained partial token material (e.g., a leaked log line truncated mid-token) — and that's already a different kind of failure. Worth fixing on consistency grounds; matches the uniform-401 discipline that `manage-appointment` and `unsubscribe` already follow (`appointments_manage.py:35` defines `_UNIFORM_401_DETAIL`).
- **Suggested fix:** In `_require_valid_token`, collapse the two failure branches into a single `HTTPException(404)`. The caller path (`/feedback/visit`) already has its own existence check immediately after, so this does not change end-user UX.

### P2 (advisory) — Aggregate dashboard / outcomes endpoints lack k-anonymity floor

- **Endpoints:**
  - `GET /api/dashboard/stats`
  - `GET /api/outcomes/aggregate`
- **File:** `backend/app/routes/dashboard.py`
- **Observed:** Both endpoints aggregate over **every** `sessions` row (no `demo` filter, no k-floor). With a low total session count and a rare barrier (e.g., `health=1`), the response reveals "exactly one worker in the system has a health barrier."
- **Expected:** Either a k-floor (suppress cells with count < 5, like `funnel_analytics.compute_community_funnel`) or, at minimum, an inclusion of `demo=1` rows so the seed sessions raise the floor.
- **Severity rationale:** In the seeded production state with 10+ demo sessions and live workers, the floor is unlikely to bite. But the *contract* is missing — there's no guard against a bad-data state that would expose a single worker's category. This is an **advisory** finding, not a fix-this-sprint blocker.
- **Suggested fix:** Apply the same k=5 suppression that `funnel_analytics` uses. Or scope the dashboard endpoint to authenticated case-managers only (move it under the advisor / admin auth boundary).

---

## Verified clean

The following classes of attack were attempted and produced the expected 403 / 404 / 422 / 410:

- **Cross-session 403 on every flagged route** (29 routes — same set T13.63 already exercises). Spot-checked manually with the parallel harness; every endpoint returns 403 with the same body shape (`"Token does not match session"` for query/body-token shape; `"Appointment belongs to another session"` for path-id shape; `"Document belongs to another session"` for documents).
- **Path-id IDOR on appointments / documents / applications:** confirmed 403 cross-session and 404 missing — the only nit is the 403/404 split itself (P2 above).
- **Confused-deputy on `POST /api/appointments` with `?session_id=A` query string + `body.session_id=B`:** FastAPI does not bind `session_id` from the query because the endpoint does not declare it as a query param; the body field wins, the auth check matches body to token, the appointment is correctly attributed to body.session_id. No surprise leak.
- **Compliance export/delete with field-name swap (`token` vs `session_token`)**: returns 422 Pydantic validation error, NOT a leak — the field name is required exact-match.
- **Compliance export with case-modified token:** 401 (the token table is case-sensitive). No `IGNORE CASE` weakness.
- **Community funnel cross-city probe via `?city=fort-worth`**: the city is resolved server-side from the caller's outcomes_records tag (`jobs_applications.py:78-99`); the query parameter is NOT honoured. K-anonymity suppression triggers (`{"__all__": {"count": null, "suppressed": true, "reason": "k_anonymity_min_5"}}`).
- **Community funnel `segment_by=session_id` injection:** returns `{}` (whitelist enforced inside `funnel_analytics`), not a per-session breakdown.
- **Manage-appointment uniform 401 oracle:** every garbage / empty / expired token returns the byte-identical 401 body. Missing `action` returns 422 (FastAPI binding error before token check) — that's a small inconsistency but does not leak appointment data.
- **Engagement unsubscribe** uniform 401 same shape.
- **Demo seed admin endpoint:** 403 on missing/wrong `X-Admin-Key`. No 401-vs-403 oracle.
- **Side-channel timing on appointment 403 vs 404:** trimmed-mean of 30 calls each: 1.07 ms (403) vs 1.04 ms (404). Delta 0.02 ms, well below any practical timing channel.
- **Aggregate dashboard reveals nothing about specific workers** beyond barrier-instance counts. The advisor inbox correctly enforces city-scoped 403s at the repository layer (`advisor/repository.py:65-86`).
- **Advisor inbox cross-city 404 vs 403:** correctly distinguishes "session does not exist" (404) from "session in another city" (403). The 403 is intended — it's the runbook section 10 C3 contract — but it does mean an advisor in city X who guesses a session_id can confirm "yes that ID exists in city Y." Documented contract; not a finding.

---

## What I could not cover

- **Browser-mediated CSRF / clickjacking:** out of scope for an API-level sweep. The endpoints do not appear to read cookies, so CSRF risk is structurally limited, but a follow-up Tier-3 should drive a real browser through the share link flow.
- **Race-condition attacks on token / appointment creation:** I did not stress concurrent calls (e.g., two threads both calling `POST /api/appointments` with the same `session_id` to test for token-binding races). The handlers all open per-request sqlite connections and the auth check runs before any write, so a race that bypasses the check is unlikely, but I did not prove its absence.
- **Staging probes:** `https://montgowork-staging-api.fly.dev` returned `503` / connection exit 28 throughout the run. All findings were reproduced on a local in-process `TestClient`. None of the findings are env-specific (all rely on handler logic that is identical across deploys), so I'm confident they apply to staging once it returns. Re-running the sweep against live staging is a useful confirmation but not a different test.
- **Audit row IDs / ETag / Cache-Control side channels:** I checked timing and response-body length on 403 vs 404 — no signal. I did not enumerate every `engagement_events` / `compliance_audit` insert path to verify a successful cross-session action never lands an audit row attributed to the wrong session. The compliance audit code (`hash_session_id` in `app.modules.compliance._audit`) writes only the hash, mitigating this.
- **Webhook auth boundary:** `POST /api/webhooks/sendgrid/events` is signed-key gated; I did not attempt to forge a SendGrid signature or replay a captured webhook. Out of scope for cross-session leak.

---

## Notable about the codebase's security posture

1. The session-owned endpoint contract is **really** consistent. Every handler uses one of two helpers — `_h.verify_token(db, sid, tok)` for the sync sqlite path or `require_session_token(db, sid, tok)` for the async path — and both raise 403 on session mismatch with identical body shape. Adding a new endpoint without going through one of those helpers is hard to do accidentally.
2. T13.63's introspection-driven test catches significantly more than I initially thought. It correctly detects `session_id`-in-path (e.g., `/api/insights/{session_id}`), `session_id`-in-query, and `session_id`-in-body, so adding a new endpoint that follows any of those three shapes is auto-covered. The only structural gap I can imagine is an endpoint whose `session_id` lives inside a *nested* Pydantic model (e.g., `body.context.session_id`) — `_body_fields()` walks the top-level `model_fields` only. None exists today, but a contributor could add one. Worth a one-line note in `_route_inventory.py` flagging this assumption.
3. The compliance audit pseudonymization (`hash_session_id`, T13.59) is good. The fact that the same hashing discipline is **not** applied to share links (P1 finding above) is the seam — the share endpoint pre-dates that discipline.
4. The uniform-401 pattern in `appointments_manage.py` and `engagement.py:_UNIFORM_401_DETAIL` is exemplary; the feedback-validate route (P2 above) is the one place where the same discipline would be cheap to apply and isn't.
5. K-anonymity is enforced at the right layer (`funnel_analytics`) and threaded through community-funnel correctly. The dashboard / outcomes-aggregate endpoints (advisory P2 above) are the inconsistent peers.

---

## Reproducer

The probe harness used for this report lives at `/tmp/probe_xsess*.py` (4 files, ~300 lines total). It's a TestClient harness with two seeded sessions and tokens; rerun via:

```bash
cd backend && .venv/bin/python /tmp/probe_xsess.py    # path-id IDOR + share + oracles
cd backend && .venv/bin/python /tmp/probe_xsess2.py   # plan / compliance / sequence / engagement
cd backend && .venv/bin/python /tmp/probe_xsess3.py   # list endpoints + confused-deputy
cd backend && .venv/bin/python /tmp/probe_xsess4.py   # introspection coverage + timing
```

If the findings here justify follow-up driver tasks, those probes can be lifted into `backend/tests/test_cross_session_data_leak.py` as proper regression tests once the fixes land.
