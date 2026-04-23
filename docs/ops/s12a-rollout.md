# S12a Rollout Runbook — Worker Companion Foundation

**Status:** staging-only. Production GA blocked until S12b T12.36 (worker
data export + right-to-delete) lands.

**Banner requirement:** Staging deployments must display
"MontGoWork worker companion (beta)" on the landing page.

---

## 1. Overview

S12a adds the backend + UI foundation for the worker-facing daily
companion:

- **13 new database tables** (see `m002_s12_worker_companion` migration)
- **5 new route modules**: `admin_flags`, `appointments`,
  `jobs_applications`, `engagement_preview`, `sendgrid_webhook`
- **APScheduler** with three cron jobs (`nightly_digest` at 02:00,
  `stall_scan` at 08:00, `appointment_reminders` every 6h)
- **Event bus** wiring: appointment outcomes + job outcomes listeners
  registered at startup
- **Nightly orchestrator** (retro -> compose -> send via SendGrid)
- **Feature flags** (env + YAML + runtime via admin endpoint)
- **SendGrid Event Webhook** with ECDSA signature verification

**Not in S12a** (deferred to S12b):

- LLM resume/cover-letter generation
- Reminder engine with cooldown / quiet hours
- Plan refresher (T12.24 — current S12a orchestrator uses a stub)
- Advisor inbox / case manager UI

## 2. Deployment Order

1. **Apply migrations**:
   ```bash
   bpsai-pair migrate --apply
   # verifies m001 -> m002 -> m003 in order
   ```
2. **Verify the 13 tables** exist:
   ```bash
   sqlite3 data/montgowork.db ".tables" | tr ' ' '\n' | grep -cE \
     '^(appointments|job_applications|resume_versions|daily_progress_snapshots|engagement_events|plan_history|outcomes_records|reminder_cooldowns|nightly_run_log|scheduler_leases|worker_unavailability|feature_flag_audit|sendgrid_events)$'
   # expect: 13
   ```
3. **Set environment variables**:
   ```bash
   ENVIRONMENT=staging
   WEB_CONCURRENCY=1                 # hard requirement — see section 5
   FEATURE_FEATURE_EMAIL_SEND_ENABLED=true
   FEATURE_FEATURE_NIGHTLY_ENABLED=true
   FEATURE_ENABLE_AI_GENERATION=false  # MUST remain false in staging
   SENDGRID_API_KEY=<scoped key>
   SENDGRID_WEBHOOK_PUBLIC_KEY=<PEM public key from SendGrid console>
   SENDGRID_FROM_EMAIL=<verified sender>
   ```
   The YAML defaults (`config/feature_flags.yaml`) already match this
   configuration for the three FEATURE flags. Env vars are the override
   source of truth per resolution order (env > runtime > yaml > default).
4. **Boot the app**:
   ```bash
   WEB_CONCURRENCY=1 uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
5. **Smoke tests** (see also section 10):
   - `curl -s $BASE/health` -> 200, body includes `"status": "ok"`
   - Create a session via the normal frontend flow
   - Render a digest preview:
     ```bash
     curl -s "$BASE/api/engagement/preview-digest?session_id=$SID&token=$TOK" \
       | jq '.section_counts'
     ```

## 3. SendGrid Setup

See `docs/ops/sendgrid-setup.md` for the full walkthrough. Quick
checklist:

- **API key**: create under SendGrid console -> Settings -> API Keys.
  Scope to **Mail Send only** (no stats, no template management).
  Store in `SENDGRID_API_KEY`.
- **SPF + DKIM**: add CNAMEs from Sender Authentication -> Domain
  Authentication. Verify before enabling nightly sends.
- **Event Webhook**:
  - Endpoint: `https://<host>/api/webhooks/sendgrid/events`
  - Enable Signed Event Webhook Requests; copy the public key (PEM)
    into `SENDGRID_WEBHOOK_PUBLIC_KEY`
  - Subscribe to: `delivered`, `bounce`, `spamreport`, `unsubscribe`
- **Rate limits**: SendGrid free tier caps at 100/day. Production tier
  required before enabling nightly digest for >50 sessions.

## 4. Feature Flag Runbook

All three S12a flags default to the YAML-provided values. Env var
overrides (prefixed `FEATURE_`) take precedence and are applied at
process start. Runtime toggles via the admin endpoint persist
in-memory for the running process only and write an audit row.

### Toggle via admin endpoint

```bash
curl -X POST "$BASE/api/admin/flags/FEATURE_NIGHTLY_ENABLED" \
  -H "X-Admin-Key: $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false, "reason": "incident-2026-04-23"}'
```

### Rate limit

`10 toggles per hour per admin token`. Exceed -> `429` with
`detail: "Rate limit exceeded"`. Window evictions are rolling.

### `ENABLE_AI_GENERATION` — extra warning

Enabling this flag writes a WARNING log line about PII / data
processing agreements. Production enablement requires a signed DPA and
a privacy-impact review; it is blocked in staging by policy until
S12b T12.36 lands.

## 5. Scheduler Constraint

**Hard requirement:** `WEB_CONCURRENCY=1`.

APScheduler in the `AsyncIOScheduler` variant runs inside the
process's asyncio loop and has no distributed lock. Spinning up two
workers would cause every scheduled job to fire twice (duplicate
emails, double accounting rows). The `enforce_single_worker()`
lifespan hook raises `RuntimeError` at startup if the env var is set
to anything other than `"1"` (unset is also allowed).

**S13 upgrade path:** the `scheduler_leases` table is already present
in m002. A distributed-lock switch can land without a schema change:
acquire `lease_name='nightly_digest'` before running, release on
completion, and honor lease expiry to survive worker crashes.

## 6. 02:00 Nightly Failure Response

If nightly emails didn't land:

1. **Check the run log**:
   ```sql
   SELECT city, sessions_processed, emails_sent, errors, duration_sec, start_ts, end_ts
   FROM nightly_run_log
   ORDER BY start_ts DESC
   LIMIT 5;
   ```
   - `errors > 0` -> per-session failures (isolated; did not abort batch)
   - `end_ts IS NULL` -> run crashed; check app logs around 02:00 CT
2. **Check send failures**:
   ```sql
   SELECT category, payload_json, created_at
   FROM engagement_events
   WHERE category = 'email_send_failed'
   AND created_at >= datetime('now', '-1 day');
   ```
3. **SendGrid side**: check SendGrid Activity tab for deliverability
   issues (bounce, block, deferred).
4. **Kill switch**: disable the nightly batch if failures are
   systemic:
   ```bash
   curl -X POST "$BASE/api/admin/flags/FEATURE_NIGHTLY_ENABLED" \
     -H "X-Admin-Key: $ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"enabled": false, "reason": "nightly-failure-2026-04-23"}'
   ```

## 7. Migration Rollback Procedure

Rollback order: **feature flag -> code deploy -> migration**.

1. **Disable the affected feature path via the flag** (section 4) so
   no new rows accumulate in the tables we're about to drop.
2. **Redeploy the previous application version** if the regression is
   in application logic. If only the schema must revert, skip.
3. **Rollback the migration**:
   ```bash
   bpsai-pair migrate --rollback --to-version 1
   # or, for m003 only:
   bpsai-pair migrate --rollback --to-version 2
   ```
   m003 is a no-op downgrade (cannot re-tighten NOT NULL). m002
   rolls back cleanly; rollback has been round-trip tested with
   seeded data (see `test_s12a_gate.test_migration_rollback_roundtrip`).
4. **State undo — in-flight data**: if rows landed in S12 tables
   between incident start and rollback, they are dropped wholesale on
   downgrade. For cases where only post-incident rows need removal:
   ```sql
   DELETE FROM engagement_events WHERE created_at > '<incident_start_iso>';
   DELETE FROM appointments      WHERE created_at > '<incident_start_iso>';
   -- repeat for job_applications, outcomes_records, etc.
   ```
   S12a does not mutate `sessions.previous_plan` (that rollback is an
   S12b concern once T12.24 plan-refresher lands), so no
   re-population of the legacy field is required.

## 8. Staging-Only Constraint

S12a ships to **staging and controlled beta only**. Blockers for
production general availability:

- **T12.36 (S12b)**: worker data export + right-to-delete endpoint.
  Without this we cannot satisfy a worker-initiated data request on
  tables populated by S12a (appointments, job_applications,
  engagement_events, resume_versions, etc.).
- **DPA sign-off** for `ENABLE_AI_GENERATION` (S12b).
- **SendGrid Pro tier** sized for >50 sessions/day.

All staging deployments must include a visible beta banner.
See `frontend/src/app/layout.tsx` for banner placement.

## 9. Known Limitations (Carry Follow-Ups)

The following are intentionally deferred to S12b — document in the
worker-facing help / changelog if any affect UX:

- **`sessions.reminders_enabled` not a column.** Bounce-triggered
  auto-disable writes an audit row in `engagement_events` and the
  orchestrator checks that audit row before sending. A first-class
  `reminders_enabled` column is on the S12b backlog.
- **`sessions.email` not a column.** The SendGrid webhook correlates
  events to sessions via `unique_args.session_id` (set per-send);
  the orchestrator pulls recipient address from
  `sessions.profile.email`.
- **Session-level city tagging** uses the first
  `outcomes_records.payload_json.city` hit, which is inefficient for
  hot paths. A dedicated `sessions.city` column is on the S12b
  backlog (cheap enforcement + index).
- **Checklist item completion** is not tracked per-day yet; the
  nightly retro sees only outcome records. Per-item completion tables
  land with T12.24 (plan refresher).

## 10. Test Hardening

Full test gates to run before a staging cut:

```bash
# Full backend suite
cd backend && .venv/bin/python -m pytest --tb=short -q

# S12a gate + admin-key scan (fast; 16 tests)
.venv/bin/python -m pytest tests/test_s12a_gate.py tests/test_s12a_admin_key_scan.py -v

# Optional: scaled load test (runs ~5s for 200 sessions)
RUN_LOAD_TESTS=1 .venv/bin/python -m pytest \
  tests/test_s12a_gate.py::test_nightly_orchestrator_scale_200_sessions_under_10_min -v

# Frontend
cd ../frontend && npm test
```

### Manual browser walk-through

Automated tests cover the API layer end-to-end. The following browser
walk-through should be performed manually before each staging cut
(orchestrator note: not covered by the gate test suite):

1. New session -> initial barrier assessment
2. Plan generation -> pathway selection
3. Appointments tab -> placeholder fill -> mark attended
4. Job applications tab -> create application
5. Daily retro -> review yesterday's outcomes
6. Digest preview -> email sections render (stall, appointments, jobs)

## 11. PR / Change Log Hook

Feature flags required for S12a staging rollout (paste into PR
description):

- `FEATURE_FEATURE_EMAIL_SEND_ENABLED=true`
- `FEATURE_FEATURE_NIGHTLY_ENABLED=true`
- `FEATURE_ENABLE_AI_GENERATION=false`
- `WEB_CONCURRENCY=1`
- `SENDGRID_API_KEY`, `SENDGRID_WEBHOOK_PUBLIC_KEY`,
  `SENDGRID_FROM_EMAIL`
