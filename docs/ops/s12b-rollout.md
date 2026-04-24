# S12b Rollout Runbook — Worker Companion Value Extensions

**Status:** **Production GA unblocked as of 2026-04-23 — S12a + S12b complete.**

**Gate tests:** `backend/tests/test_s12b_gate.py`
(+ `test_s12b_gate_endpoints.py`), `backend/tests/test_s12b_admin_key_scan.py`.
26 gate assertions, 16 admin-key scan coverage points,
load test gated on `RUN_LOAD_TESTS=1`.

**Baseline:** backend 3226/3228 pass (2 pre-existing carry-overs,
documented in Section 11), frontend 946/946 pass. Zero S12a regressions.

---

## 1. Overview

S12b extends the S12a worker-companion foundation with the value +
compliance layer:

- **4 new database migrations** (m004 used_tokens, m005 sessions.demo,
  m006 compliance tombstones, m007 advisor_tokens)
- **5 new route modules**: `advisor_inbox`, `appointments_manage`,
  `compliance`, `documents`, `engagement`
- **LLM-gated resume + cover-letter builders** (T12.15/T12.16)
- **Signed single-use manage-appointment links** with key rotation
  (T12.10b)
- **Worker data export + right-to-delete + retention sweep** (T12.36)
- **Case-manager advisor inbox** (T12.31) with per-token city scoping
- **Transactional appointment emails** (T12.7a) @ 24h + 1h reminders
- **Plan refresher with 20-row history cap** (T12.24)
- **Weekly review composer** (T12.22a)
- **Reminder engine with cooldown** (T12.19) wired into the
  nightly orchestrator
- **Demo seed** — 10 demo sessions (5 per city × 5 stall states)
  with `sessions.demo=TRUE` column guard
- **Documents UI pages** (T12.28), **Jobs kanban** (T12.27),
  **Nav + stall banner** (T12.30), case-manager "Needs Attention"
  card (T12.31 frontend)

**Already in S12a** (prerequisites): 13 S12 tables, APScheduler,
SendGrid webhook, event bus, nightly orchestrator skeleton, feature
flags, admin-flag endpoint.

## 2. Deployment Order

1. **Apply migrations**:
   ```bash
   bpsai-pair migrate --apply
   # verifies m001 -> m002 -> m003 -> m004 -> m005 -> m006 -> m007 in order
   ```
2. **Verify the new S12b schema integrity**:
   ```bash
   sqlite3 data/montgowork.db "SELECT MAX(version) FROM schema_migrations;"
   # expect: 7

   sqlite3 data/montgowork.db "PRAGMA table_info(sessions);" | grep demo
   # expect: ...|demo|BOOLEAN|1|FALSE|0

   sqlite3 data/montgowork.db ".tables" | tr ' ' '\n' | \
     grep -E '^(advisor_tokens|compliance_audit|used_tokens)$' | wc -l
   # expect: 3

   sqlite3 data/montgowork.db \
     "SELECT sql FROM sqlite_master WHERE name='idx_advisor_tokens_active';"
   # expect: partial index on (advisor_id, city) WHERE revoked_at IS NULL
   ```
3. **Set environment variables** (all S12a vars plus the S12b additions):
   ```bash
   # S12a carry-forward
   ENVIRONMENT=production
   WEB_CONCURRENCY=1
   SENDGRID_API_KEY=<scoped key>
   SENDGRID_WEBHOOK_PUBLIC_KEY=<PEM>
   SENDGRID_FROM_EMAIL=<verified sender>

   # S12b additions
   APPOINTMENT_TOKEN_SECRET=<32+ byte secret>
   # Only set during rotation window (see Section 4):
   # APPOINTMENT_TOKEN_SECRET_OLD=<previous secret>

   COMPLIANCE_TOKEN_SECRET=<32+ byte secret>
   # Rotate every 6 months; overlap with *_OLD for 48h (see Section 5).

   # Feature flags (YAML already has defaults matching prod intent)
   FEATURE_FEATURE_EMAIL_SEND_ENABLED=true
   FEATURE_FEATURE_NIGHTLY_ENABLED=true
   FEATURE_ENABLE_AI_GENERATION=false
   # ^ production default — ONLY flip per Section 3 after DPA sign-off.
   ```
4. **Boot the app**:
   ```bash
   WEB_CONCURRENCY=1 uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
5. **Smoke tests**:
   - `curl -s $BASE/health` → 200, `{"status": "ok"}`
   - Gate tests: `cd backend && .venv/bin/python -m pytest \
     tests/test_s12b_gate.py tests/test_s12b_gate_endpoints.py \
     tests/test_s12b_admin_key_scan.py -v`
   - Frontend: `cd frontend && node_modules/.bin/vitest run`
     (no `npm test` script — see Section 11 carry-over #9).

## 3. LLM Feature Flag Enablement (`ENABLE_AI_GENERATION`)

**Production default: `false`.** The resume + cover-letter builders
(T12.15, T12.16) fall back to deterministic template output when the
flag is false. Flipping to true enables the `_call_llm` hook, which
sends worker PII to the configured LLM provider.

### Pre-flight (blocking)

Before flipping in production:
- Signed DPA (data processing agreement) with the LLM provider on file
- Privacy-impact review completed and archived in the compliance log
- Staging soak >= 7 days with `ENABLE_AI_GENERATION=true` and no
  `engagement_events.category='email_send_failed'` spike
- On-call rotation aware of rollback lever

### Enable

```bash
curl -X POST "$BASE/api/admin/flags/ENABLE_AI_GENERATION" \
  -H "X-Admin-Key: $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true, "reason": "ga-rollout-YYYY-MM-DD"}'
```

### Expected audit signals

1. **WARNING log line** on the API host:
   `AI generation enables LLM processing of worker PII — verify
   data processing agreement is active`
2. **Audit row** in `feature_flag_audit`:
   ```sql
   SELECT flag_name, old_value, new_value, actor_token_hash, reason,
          source_ip, timestamp
   FROM feature_flag_audit
   WHERE flag_name = 'ENABLE_AI_GENERATION'
   ORDER BY id DESC LIMIT 1;
   ```
   `actor_token_hash` is the **SHA256 hex digest** of the admin
   header — the raw header is never stored.
3. Verified by the gate assertion
   `test_flipping_ai_generation_writes_audit_row_and_warns`.

### Rollback

```bash
curl -X POST "$BASE/api/admin/flags/ENABLE_AI_GENERATION" \
  -H "X-Admin-Key: $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false, "reason": "incident-YYYY-MM-DD"}'
```

Rollback takes effect for every process instance with the next
runtime-override poll (current process: immediate via in-memory
override; restarted workers: re-read YAML, which already defaults
to `false`). Queued nightly-digest jobs pick up the new value on
their next call to `feature_flags.is_enabled`.

## 4. Appointment Token Rotation (`APPOINTMENT_TOKEN_SECRET`)

Single-use manage-appointment tokens (T12.10b) are HMAC-SHA256 signed
under `APPOINTMENT_TOKEN_SECRET`. The verify path tries **every active
secret** so a rotation overlap window lets pre-rotation tokens
continue to validate while new tokens are minted under the new secret.

### Rotation cadence

- **6 months** between scheduled rotations
- **Immediate** rotation on any suspected leak
- **7-day overlap window** — matches the token TTL
  (`_DEFAULT_TTL_SEC = 7 * 24 * 3600`)

See `docs/ops/appointment-token-rotation.md` for the full walkthrough.

### Rotation steps

1. Generate a new 32-byte secret:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
2. **Before the cutover** — add the current secret as OLD. This lets
   verify accept both during overlap:
   ```bash
   export APPOINTMENT_TOKEN_SECRET_OLD="$APPOINTMENT_TOKEN_SECRET"
   export APPOINTMENT_TOKEN_SECRET="<new secret>"
   systemctl restart montgowork-api
   ```
3. **Verify old-era tokens still accept**:
   Send a test email from `scripts/` that mints a token, then
   consume it at `/api/appointments/manage?token=...&action=view`.
   Gate coverage: `test_old_secret_accepted_during_rotation_window`.
4. **Wait >= 7 days** so every in-flight token has expired.
5. **Close the window** — drop the OLD variable:
   ```bash
   unset APPOINTMENT_TOKEN_SECRET_OLD
   systemctl restart montgowork-api
   ```
6. **Verify old-era tokens now reject**:
   Mint a token with only OLD set, then try to verify it after
   closing the window — expect `TokenInvalid`. Gate coverage:
   phase 3 of `test_old_secret_accepted_during_rotation_window`.

### Incident response (leak detected)

- Roll the secret immediately (skip step 2; cutover directly)
- Invalidate all outstanding tokens by omitting OLD from step 2
- Query `used_tokens` for anomalous replay attempts:
  ```sql
  SELECT appointment_id, used_at, action, COUNT(*)
  FROM used_tokens
  WHERE used_at > '<incident_start>'
  GROUP BY appointment_id, action
  HAVING COUNT(*) > 1;
  -- Any row is a potential replay attempt.
  ```

## 5. Compliance Operations

See `docs/ops/compliance-operations.md` for the full operator guide.
Runbook summary below.

### Worker data export

Worker-initiated via `POST /api/compliance/export`:
```bash
curl -X POST "$BASE/api/compliance/export" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "<sid>", "session_token": "<feedback_token>"}'
```

Returns `{"archive_id": ..., "download_url": "/api/compliance/export/
download?token=...", "expires_in_sec": 86400}`. The download link is
single-use and expires in 24 hours. The archive includes:
- `data.json` — every row from the 13 S12 tables + `sessions` +
  `record_profiles`, sorted-key JSON for diffing
- `summary.md` — plaintext summary of the scope + contents

Audit rows in `compliance_audit`:
- `action='export_requested'` on POST
- `action='export_downloaded'` on GET

### Full delete (right-to-delete)

```bash
curl -X POST "$BASE/api/compliance/delete" \
  -H "Content-Type: application/json" \
  -d '{
        "session_id": "<sid>",
        "session_token": "<feedback_token>",
        "confirm": "DELETE",
        "reason": "worker_request"
      }'
```

Cascades a `DELETE FROM sessions WHERE id = ?` with FKs enforced.
All 13 S12 tables (appointments, job_applications, resume_versions,
daily_progress_snapshots, engagement_events, plan_history,
outcomes_records, reminder_cooldowns, worker_unavailability,
scheduler_leases, feature_flag_audit, sendgrid_events) clear via
cascade. `record_profiles` is cleared explicitly because m001
predates the S12a FK contract.

Audit row: `action='full_delete'`, `session_id_hash` is
`SHA256(session_id)` — the raw id is NOT kept on the audit row
(since the session no longer exists).

### Selective delete (category tombstone)

```bash
curl -X POST "$BASE/api/compliance/delete/selective" \
  -H "Content-Type: application/json" \
  -d '{
        "session_id": "<sid>",
        "session_token": "<feedback_token>",
        "category": "criminal_record"
      }'
```

Category map:
- `criminal_record` → `record_profiles`

Soft-deletes via `deleted_at` + `deleted_reason` tombstone columns
(m006). Subsequent reads filter via `WHERE deleted_at IS NULL`.

### Retention sweep

Runs nightly as the last step of `scripts.nightly_digest.run_nightly_digest`
(post-digest, post-audit). Purges sessions with
`expires_at < now - 90d`:
```python
from app.modules.compliance.retention import (
    RETENTION_GRACE_DAYS, retention_sweep,
)
purged = retention_sweep(db_path="/path/to/db")
# returns list of purged session_ids
```

Per-purge audit: `action='retention_purge'`. Batch is robust —
a single failure never aborts the loop. Verified by
`test_retention_sweep_wired_into_nightly_orchestrator`.

### `COMPLIANCE_TOKEN_SECRET` rotation

The export download token uses the same HMAC-SHA256 + kid pattern
as `APPOINTMENT_TOKEN_SECRET`. Rotation cadence: 6 months. Overlap
window: 24h (matches export TTL). Procedure mirrors Section 4.

## 6. Advisor Auth Issuance

See `docs/security/advisor-auth.md` for the full policy. Quick ops
summary:

### Token format

`mw_adv_<base58>` — plaintext is shown to the advisor ONCE on issuance
and NEVER logged / stored server-side. The server keeps
`SHA256(plaintext)` as the `advisor_tokens.token_hash` PK.

### Issuance (SQL fallback — operator CLI is a future ticket;
see carry-over #8)

```sql
INSERT INTO advisor_tokens
    (token_hash, advisor_id, city, issued_at, revoked_at, expires_at)
VALUES
    (
        lower(hex(sha256('<plaintext>'))),    -- or compute externally
        'adv-jane-mtg',
        'montgomery',
        datetime('now'),
        NULL,
        NULL                                  -- NULL = no time-based expiry
    );
```

Share the plaintext `mw_adv_<base58>` token with the advisor via
secure channel (1Password shared vault, not email or chat).

### Revocation (<= 5-minute SLA)

```sql
UPDATE advisor_tokens
SET revoked_at = datetime('now')
WHERE advisor_id = 'adv-jane-mtg' AND revoked_at IS NULL;
```

The validate path rejects revoked rows — no cache, no TTL to wait
out. Also available programmatically:

```python
from app.core.advisor_auth import revoke_token
revoke_token(db_path, "adv-jane-mtg")
```

### Rotation cadence

6 months. No dual-secret window — tokens are per-row so a rotation
is: issue new row, share new plaintext with advisor, revoke old row.

### Token scope

`city` is the claim — every request goes through the repository
layer with the advisor's city as a filter. Cross-city access returns
HTTP 403 (verified by `test_advisor_cross_city_returns_403`).

## 7. Nightly Job Failure Response

If the 02:00 CT nightly digest cron fails:

### 1. Locate the failure

```sql
-- Most recent runs, newest first.
SELECT city, sessions_processed, emails_sent, errors,
       duration_sec, start_ts, end_ts
FROM nightly_run_log
ORDER BY start_ts DESC
LIMIT 10;
```

- `errors > 0` → per-session failures (isolated; batch continued)
- `end_ts IS NULL` → run crashed; check app logs around 02:00 CT

### 2. Inspect per-session failures

```sql
SELECT session_id, category, payload_json, created_at
FROM engagement_events
WHERE category IN ('email_send_failed', 'digest_compose_failed')
  AND created_at >= datetime('now', '-1 day')
ORDER BY created_at DESC;
```

### 3. Check the retention sweep

Retention runs as the final step. If it fails, the digest batch
already succeeded — grep logs for `retention sweep failed`.
Rollback is not required; the sweep is idempotent and rows past
90 days get caught on the next run.

### 4. SendGrid side

Check the SendGrid Activity tab for deliverability issues (bounce,
block, deferred). Webhook events land in `sendgrid_events`:

```sql
SELECT category, COUNT(*)
FROM sendgrid_events
WHERE received_at >= datetime('now', '-1 day')
GROUP BY category;
```

### 5. Kill switch

If failures are systemic:

```bash
curl -X POST "$BASE/api/admin/flags/FEATURE_NIGHTLY_ENABLED" \
  -H "X-Admin-Key: $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false, "reason": "nightly-failure-YYYY-MM-DD"}'
```

### 6. Manual re-run (after a fix)

```bash
cd backend && .venv/bin/python -m scripts.nightly_digest \
  --cities montgomery,fort-worth
```

The script is idempotent on resume: sessions that already got
today's digest are skipped via the `nightly_run_log` check.

## 8. APScheduler Single-Worker Constraint

**Hard requirement:** `WEB_CONCURRENCY=1`.

Same constraint as S12a. `enforce_single_worker()` raises at startup
if the env var is anything other than `"1"` (unset also allowed).
Verified by `test_scheduler_rejects_web_concurrency_2`.

The three S12a jobs remain registered under S12b:
- `nightly_digest` — 02:00 CT (handler = real orchestrator, not stub;
  verified by `test_nightly_digest_handler_is_real_orchestrator`)
- `stall_scan` — 08:00 CT
- `appointment_reminders` — every 6 hours

S13 upgrade path: `scheduler_leases` table already present (m002) —
distributed lock switch can land without a schema change.

## 9. Migration Rollback

Rollback order: **feature flag → code deploy → migration**.

### Rollback selector

```bash
# Revert m005+m006+m007 (leave m004 in place — it is schema-only and
# breaking nothing):
bpsai-pair migrate --rollback --to-version 4

# Revert everything back to S12a baseline:
bpsai-pair migrate --rollback --to-version 3

# Revert everything back to pre-S12:
bpsai-pair migrate --rollback --to-version 1
```

Round-trip verified by `test_s12b_migrations_round_trip` — the gate
applies, rolls back to version 4, and re-applies without data loss
on the S12a baseline tables.

### Data concerns

- **m005 rollback** drops `sessions.demo`. Demo rows stay as sessions;
  the T12.12 funnel guard no-ops when the column is absent (see
  `funnel_queries.has_demo_column`), so community funnel analytics
  would start including demo sessions. Purge demo rows before
  rollback:
  ```sql
  DELETE FROM sessions WHERE id LIKE 's12b-demo-%';
  ```
- **m006 rollback** drops `compliance_audit` + the three tombstone
  columns. Any active tombstones become real rows again (soft-delete
  becomes undone). Before rollback, either hard-delete tombstoned
  rows:
  ```sql
  DELETE FROM record_profiles WHERE deleted_at IS NOT NULL;
  -- repeat for resume_versions, engagement_events
  ```
  or preserve them in an out-of-band archive.
- **m007 rollback** drops `advisor_tokens`. All active advisors lose
  access. Re-issuance required after re-apply.

## 10. GA Readiness Checklist

| AC item | Status | Evidence |
|---------|--------|----------|
| Full backend suite passes | PASS | 3226/3228 (2 pre-existing carry-overs documented) |
| Frontend suite passes | PASS | 946/946 |
| Zero S12a regressions | PASS | S12a gate still 16 passed + 1 skipped |
| All S12b routes respond | PASS | `test_all_s12b_routers_in_all_routers` |
| Scheduler under `WEB_CONCURRENCY=2` rejects | PASS | `test_scheduler_rejects_web_concurrency_2` |
| m005/m006/m007 migration round-trip | PASS | `test_s12b_migrations_round_trip` |
| `ENABLE_AI_GENERATION=false` default | PASS | `test_ai_generation_default_off` |
| Flipping emits audit row + warning | PASS | `test_flipping_ai_generation_writes_audit_row_and_warns` |
| Token rotation rehearsal | PASS | `test_old_secret_accepted_during_rotation_window` + runbook §4 |
| Compliance operations walkthrough | PASS | Runbook §5 + `test_compliance_endpoints_reject_missing_token` |
| Admin-key scan | PASS | `test_no_hardcoded_secrets_in_s12b_production_files` + manual grep sweep |
| Runbook present | PASS | This document |
| GA unblocked confirmation | PASS | **Section 12** below |

The **manual browser walk-through** listed in the original AC is the
one item not automated by the gate — it requires a human click-through
of: daily digest → jobs kanban → resume generation → cover letter →
PDF download → stall alert → advisor note → advisor inbox. Execute
against staging before final cutover.

## 11. Known Limitations (Carry-Forwards — Do Not Block GA)

The following are known and documented; they do not block production
GA but are tracked for follow-up sprints:

1. **`app/routes/__init__.py` has 27+ imports** (pre-existing arch
   warning that predates T12.16). Decomposition ticket deferred —
   arch-check is warning-only for this file.
2. **`sessions.reminders_enabled` / `.email` / `.city` columns are
   not first-class** — handled via row patterns (audit events for
   reminders, `profile.email`, first `outcomes_records.payload_json.
   city` hit). S13 ticket to promote each to a column + index.
3. **`sessions.previous_plan` deprecated in S13** — T12.24
   introduces dual-write; previous field still read until migration.
4. **`_call_llm` placeholders** (T12.15, T12.16) are gated by
   `ENABLE_AI_GENERATION=false` in production and return deterministic
   template output. Flipping the flag requires DPA sign-off per §3.
5. **`test_evidence_collector::test_outcomes_logged_in_range`** — UTC
   vs local-date midnight flake, affects a single test. Own ticket
   (not S12b scope). Present on clean checkout.
6. **`test_contract_credit_api::test_provider_simple_input_fields_
   unchanged`** — sibling `credit-assessment` repo missing `jwt`
   import. Environmental failure, present on clean checkout.
7. **`DigestResult.module_status`** (T12.25b) exposed but not
   rendered into the digest body. Planned advisor-inbox seam;
   consumed by T12.31 list view.
8. **Advisor token operator CLI** — currently inserted via SQL
   (documented in §6). Operator CLI is a future ticket; SQL path
   is sufficient for GA rollout.
9. **Frontend has no `test` script in `package.json`** — invoke
   vitest directly: `cd frontend && node_modules/.bin/vitest run`.
   Script-add PR is a future chore.
10. **Stall banner uses `counts.stall > 0` proxy** (T12.30) —
    awaits backend exposure of `stall_level` on the digest preview
    endpoint (current contract only returns `section_counts`).

## 12. Production GA Confirmation

**As of 2026-04-23, production GA is UNBLOCKED — S12a + S12b complete.**

- **S12a (Worker Companion Foundation)**: 25/25 tasks complete, merged
  to main (`4a569fb`), gate tests passing.
- **S12b (Worker Companion Value Extensions)**: 25/25 tasks complete,
  on branch `sprint/s12b-value-extensions`, gate tests passing.
- **Prior production blockers resolved**:
  - T12.36 (worker data export + right-to-delete) — shipped
  - DPA sign-off prerequisite for `ENABLE_AI_GENERATION` — documented
    in §3 (operator enables post-DPA; default remains off)
  - SendGrid Pro tier capacity — operational dependency, not code
    (coordinate with operations on quotas)

### PR / Change-Log Hook

Paste into the PR description for the S12b merge:

```
Feature flags / env vars required for S12b production rollout:
- FEATURE_FEATURE_EMAIL_SEND_ENABLED=true
- FEATURE_FEATURE_NIGHTLY_ENABLED=true
- FEATURE_ENABLE_AI_GENERATION=false    (remains off until DPA per §3)
- WEB_CONCURRENCY=1
- APPOINTMENT_TOKEN_SECRET                (required; rotation §4)
- COMPLIANCE_TOKEN_SECRET                 (required; rotation §5)
- SENDGRID_API_KEY, SENDGRID_WEBHOOK_PUBLIC_KEY, SENDGRID_FROM_EMAIL

Gate tests (26 assertions, 16 admin-key coverage):
- backend/tests/test_s12b_gate.py
- backend/tests/test_s12b_gate_endpoints.py
- backend/tests/test_s12b_admin_key_scan.py

Baseline: backend 3226/3228, frontend 946/946.
```

---

## 13. Appendix — Related Runbooks

- `docs/ops/s12a-rollout.md` — S12a foundation runbook (prerequisite)
- `docs/ops/appointment-token-rotation.md` — appointment token detail
- `docs/ops/compliance-operations.md` — export/delete/retention detail
- `docs/ops/sendgrid-setup.md` — SendGrid webhook + sender config
- `docs/security/advisor-auth.md` — advisor identity model
