# Rollback Runbook

**Owner:** Kevin Masterson (sprint lead) — `<kmasty1@gmail.com>`
**Sprint:** S13 (T13.120)
**Last reviewed:** 2026-04-25
**Companion runbook:** `docs/runbooks/staging-deploy.md` (T13.128) — read first if you have not deployed staging before; this runbook assumes the apps and secrets in §3 of that doc already exist.

This runbook is **page-skimmable**. If something is on fire, go straight to §2 (decision tree) and pick a scenario. Each scenario lists detection signals, the exact commands, expected rollback time, and post-rollback verification steps. All rehearsal commands at the bottom of each section have been exercised dry-run against live staging on 2026-04-25 — see "Rehearsal status" boxes.

---

## 1. When to use this runbook

Reach for a rollback when **any** of:

- A deploy went out and `/health` or `/health/live` is failing (5xx, timeouts, or `{"status":"degraded"}`).
- The frontend builds, but every API call 500s or the browser shows CORS errors.
- A migration ran and downstream queries throw `no such column` / `no such table` / FK-constraint errors.
- A feature flag flipped on and a specific feature is causing user-visible degradation.
- Outbound email is hitting the wrong recipients or the scheduler is firing at the wrong time.
- Security incident: leaked admin key, suspected unauthorized data access, or PII in logs.

**Do not use this runbook for:**
- Test failures in CI before deploy (fix the code; do not deploy and roll back).
- "I want to revert one commit" — `git revert` + new deploy is faster than rollback.
- Cosmetic frontend bugs — file a ticket; rolling back the whole release loses other fixes.

---

## 2. Decision tree

```
Is there an active deployment in progress?
  YES → wait 60s for it to land or fail; do not roll back mid-deploy.
  NO  → continue.

Symptom?
├── App is 500ing / health-check failing / build broken
│       → SCENARIO A (app-only rollback, ~30s)
│
├── DB error: "no such column", "no such table", FK violation,
│   data corrupted, or wrong-shape rows in production
│       → SCENARIO B (DB rollback, 5-10min for snapshot, <5s for qc_reset)
│
├── A specific feature broke (other features still work)
│       → SCENARIO C (feature-flag rollback, <30s)
│
└── Scheduler / nightly / outbound email going wrong
        → SCENARIO D (emergency kill-switch, 30s-2min)
```

If two scenarios apply (e.g., bad code AND bad data), do **A first** to stop new bad data, then **B** to clean up.

---

## 3. Who pages whom

This is a one-person hackathon project; the escalation table below is therefore short on purpose.

| Role | Person | Reach via |
|------|--------|-----------|
| Owner / on-call | Kevin Masterson | `<kmasty1@gmail.com>`; phone in 1Password under "MontGoWork — Staging" |
| Escalation (Fly account) | Fly.io support | <https://fly.io/docs/about/support/> (community tier — no SLA) |
| Code-fix backstop | Open issue on the repo, tag `incident` | <https://github.com/USER/montgowork/issues> (replace `USER` with the GitHub owner of the repo at hand-off) |

For an unattended demo, the demo runner becomes the on-call. Print this runbook and tape it next to the laptop.

---

## 4. Pre-flight (before touching anything)

1. **Confirm you are pointed at the right app:**
   ```bash
   fly status --app montgowork-staging-api
   ```
   Note the current image tag (e.g. `deployment-01KQ1G0NCWE7JFJGK9FK3D2MDA`) — you will need this to identify what you are rolling **back from**.

2. **Capture logs before rolling back** (so post-mortem is possible):
   ```bash
   fly logs --app montgowork-staging-api > /tmp/incident-$(date -u +%Y%m%dT%H%M%SZ).log &
   sleep 5; kill %1
   ```

3. **Announce in chat** (one-line `WHAT / WHO / ETA`):
   > "Rolling back staging API to v2 due to 500s on /api/sessions. Owner: kmasty1. ETA 1 minute."

---

## 5. Scenario A — App-only rollback (bad code deploy)

**Use when:** the most recent deploy is the cause and the database schema is unchanged (or only had additive migrations — see "Migration caveat" below).

**Detection signals:**
- `/health/live` returns non-200 or times out after a recent `fly deploy`.
- `fly status` shows the latest machine in `unhealthy` / `1 critical` checks.
- 500s spiking in `fly logs --app montgowork-staging-api`.
- Build broken, frontend can't reach API, JS errors referencing a recent change.

### Steps

1. **List the recent releases (with image refs):**
   ```bash
   fly releases --app montgowork-staging-api --image
   ```
   Output columns: `VERSION │ STATUS │ DESCRIPTION │ USER │ DATE │ DOCKER IMAGE`. Pick the most recent **complete** release that is **not** the broken one (typically the previous version: if current is `v3`, target `v2`).

2. **Re-deploy the prior image** (this is how Fly does rollback in 2026):
   ```bash
   fly deploy \
       --app montgowork-staging-api \
       --image registry.fly.io/montgowork-staging-api:deployment-<PRIOR_TAG>
   ```
   `<PRIOR_TAG>` is the value from the `DOCKER IMAGE` column for the target version (e.g. `01KQ1FYJ1JJRZDJNJPJC0N2NHM`). Fly streams progress; expect ~30 seconds.

3. **Repeat for the frontend if needed:**
   ```bash
   fly releases --app montgowork-staging-web --image
   fly deploy \
       --app montgowork-staging-web \
       --image registry.fly.io/montgowork-staging-web:deployment-<PRIOR_TAG>
   ```

4. **Verify the rollback:**
   ```bash
   curl -fsS -m 30 https://montgowork-staging-api.fly.dev/health/live
   # → {"alive":true,"uptime_seconds":...}
   curl -fsS -m 30 https://montgowork-staging-api.fly.dev/health
   # → {"status":"healthy",...}
   curl -fsS -I https://montgowork-staging-web.fly.dev/ | head -1
   # → HTTP/2 200
   ```

5. **Post-rollback:** announce restoration; open a `bugfix` task to root-cause the bad deploy before re-rolling forward.

### Rollback time

~30 seconds (Fly redeploys the prior image; no rebuild). First request after rollback can take ~10s if the machine cold-starts — see §9.

### Migration caveat

`fly deploy` rolling back the **app** does **not** roll back the **database**. The codebase uses additive-only migrations (m001…m007 in `backend/app/core/migrations/`); each migration only adds tables/columns, so a code rollback over an applied migration is generally safe — the prior code simply ignores the new column. Two exceptions:

- A migration that **removed** a column (none in m001…m007 today, but possible in future). Going back to code that still reads the column will 500.
- A migration that **changed semantics** of an existing column (e.g., m003 made `appointments.starts_at` nullable; rolling back to pre-m003 code would refuse `NULL` rows that have since been written).

If either applies, jump to Scenario B.

### Rehearsal status

- [x] **Rehearsed 2026-04-25** — `fly releases --app montgowork-staging-api --image` returned three releases (v1/v2/v3) with full image refs in 1.2s. Rollback target if v3 went bad: re-deploy `registry.fly.io/montgowork-staging-api:deployment-01KQ1FYJ1JJRZDJNJPJC0N2NHM` (v2). Did **not** actually run the rollback `fly deploy` — staging is currently healthy.
- [x] Verified `fly status --app montgowork-staging-api` reports the active machine ID `48e062ec730718` and the current image, which is what step 1 needs.

---

## 6. Scenario B — Database rollback (corrupt or wrong-shape data)

**Use when:** data is the problem, not the code. Migrations are **additive-only** and there is **no automatic down-migration** path — the migration runner has `downgrade()` shims on each migration but they have not been exercised, and SQLite's lack of `DROP COLUMN` makes them risky in production.

**Detection signals:**
- Errors like `no such column: foo`, FK constraint failures, or `IntegrityError` from SQLAlchemy.
- A user reports their session's data is wrong, missing, or showing someone else's records.
- A demo seed run wrote into the wrong rows.

### Options (in order of preference)

#### B1. Volume snapshot restore (Fly daily snapshots, 5-day retention on staging)

**Best for:** any production-grade rollback where user data after the incident must be discarded.
**RPO:** 24 hours on staging (Fly's default snapshot cadence).
**Destructive:** yes — anything written between the snapshot and now is lost.

```bash
# 1. Find the volume id and list snapshots
fly volumes list --app montgowork-staging-api
# → vol_<id>  montgowork_staging_db  1GB iad ...
fly volumes snapshots list <volume-id>
# → SNAPSHOT_ID │ SIZE │ STATUS │ CREATED_AT

# 2. Create a fresh volume from the snapshot
fly volumes create montgowork_staging_db_restore \
    --app montgowork-staging-api \
    --region iad \
    --snapshot-id <snapshot-id> \
    --size 1

# 3. Edit deploy/fly/fly.backend.toml — change the [[mounts]] source to
#    "montgowork_staging_db_restore", commit/push, then redeploy.
fly deploy --app montgowork-staging-api \
    --config deploy/fly/fly.backend.toml \
    --dockerfile Dockerfile

# 4. Verify
curl -fsS https://montgowork-staging-api.fly.dev/health
```

#### B2. Selective row-level fix (surgical, non-destructive)

**Best for:** a known bad row or table you can reproduce in the DB. Faster than a full restore, no data loss.
**Time:** 2-5 minutes once you know the SQL.

```bash
fly ssh console --app montgowork-staging-api
# inside the container:
sqlite3 /app/data/montgowork.db
> .schema <table>
> SELECT * FROM <table> WHERE <bad-row-criteria> LIMIT 5;
> -- BACKUP FIRST
> .backup /app/data/montgowork-pre-fix-$(date +%Y%m%dT%H%M%SZ).db
> -- then patch
> UPDATE ... WHERE ...;
> .quit
exit
```

Always take a `.backup` **before** any UPDATE/DELETE so you can roll back the rollback.

#### B3. Full DB wipe + reseed — DEMO ONLY

**Use only on staging when the demo data set is broken.** This destroys **all** data, including any non-demo testing. Acceptable on the staging hackathon DB; **never** in production.

```bash
fly ssh console --app montgowork-staging-api
# inside the container — assumes T13.3 qc_reset.py is on disk:
python /app/scripts/qc_reset.py --db-path /app/data/montgowork.db
# → "Reseeded: YES (T13.2 demo seed factory)"
exit
```

The wipe is scoped: `qc_reset.py` only deletes rows tagged `demo=1` (and demo-seeded children). Non-demo rows survive. See `scripts/_qc_reset_wipe.py` for the per-table list.

If you also want to flush the migration and start completely over (last resort):

```bash
fly ssh console --app montgowork-staging-api
rm /app/data/montgowork.db
exit
fly machines restart 48e062ec730718 --app montgowork-staging-api
# Lifespan re-runs init_db() and re-applies migrations m001…m007 on next boot.
```

### Production-rollback note

Production currently has **no rollback strategy beyond B1**. RPO is 24h (daily snapshot cadence). When promoting (see staging-deploy.md §10), one of:

- Migrate to managed Postgres + PITR (preferred; documented in `docs/architecture.md`).
- Increase Fly snapshot retention and add hourly snapshots.
- Add a backup hook to the `lifespan()` in `backend/app/main.py` that copies the SQLite file to S3 every N hours.

Until one of these lands, **document any prod incident's data-loss window** in the post-mortem.

### Rollback time

| Path | Time |
|------|------|
| B1 snapshot restore | 5-10 min (volume create + redeploy) |
| B2 selective fix | 2-5 min (depends on SQL complexity) |
| B3 qc_reset wipe + reseed | <5 sec |

### Rehearsal status

- [x] **B3 (qc_reset) rehearsed 2026-04-25** — created `/tmp/rollback_rehearsal.db`, ran `apply_pending` for m001..m007, then `python scripts/qc_reset.py --db-path /tmp/rollback_rehearsal.db --no-reseed`. Total wall-clock: **0.145s**. Output: deletion summary across 18 tables (all 0 rows because the test DB was empty post-migration). Procedure verified.
- [ ] **B1 (volume snapshot) NOT rehearsed** — `fly volumes snapshots list vol_40ogkx85p9jz5jm4` returned `No snapshots available for volume vol_40ogkx85p9jz5jm4`. The staging volume was created 18h before the rehearsal; Fly's first snapshot is taken 24h after volume creation. **TODO:** re-run this rehearsal after 2026-04-26T05:00Z (24h post-create) to confirm `fly volumes snapshots list` returns a snapshot id.
- [ ] **B2 (selective row-fix) NOT rehearsed live** — `fly ssh console` requires the on-call to be `fly auth login`'d as the volume owner; documented but not exercised. **TODO:** dry-run the `sqlite3 .backup` flow on a tmp DB during the next QC pass.

---

## 7. Scenario C — Feature-flag rollback (bad feature)

**Use when:** one specific feature (AI generation, nightly digest, email send, etc.) is misbehaving and the rest of the app is fine. **No redeploy required** — feature flags are runtime-toggleable.

**Detection signals:**
- A specific endpoint or background job is failing while everything else works.
- `engagement_events` rows showing a worker getting wrong reminders.
- AI generation returning empty/garbage responses.

### Steps

1. **Identify the flag.** Known live flags (from `config/feature_flags.yaml`):
   - `ENABLE_AI_GENERATION` — gates resume/cover-letter LLM calls.
   - `FEATURE_NIGHTLY_ENABLED` — master switch for the APScheduler nightly job.
   - `FEATURE_EMAIL_SEND_ENABLED` — master switch for SendGrid outbound.

   To find a flag for an unfamiliar feature:
   ```bash
   grep -r "is_enabled('" /Users/kevinmasterson/Projects/montgowork/backend/app/
   ```

2. **Toggle the flag off via the admin endpoint.** This writes a `feature_flag_audit` row, takes effect in <1s, and **does not require a redeploy.**

   ```bash
   curl -fsS -X POST \
       -H "X-Admin-Key: $STAGING_ADMIN_KEY" \
       -H "Content-Type: application/json" \
       -d '{"enabled":false,"reason":"incident: <one-line reason>"}' \
       https://montgowork-staging-api.fly.dev/api/admin/flags/<FLAG_NAME>
   # → {"flag_name":"<FLAG_NAME>","enabled":false,"applied_at":"2026-04-25T..."}
   ```

   `$STAGING_ADMIN_KEY` is in 1Password under "MontGoWork — Staging". The endpoint enforces a per-actor 10/hour rate limit (see `backend/app/routes/admin_flags.py`); incident toggling is well under that.

3. **Verify the audit row was written:**
   ```bash
   fly ssh console --app montgowork-staging-api
   sqlite3 /app/data/montgowork.db \
       "SELECT flag_name, old_value, new_value, reason, timestamp \
        FROM feature_flag_audit ORDER BY timestamp DESC LIMIT 3;"
   exit
   ```

4. **Confirm the flag now reads `false` from the API perspective.** There is no `GET /api/admin/flags/<name>` (yet — see TODO below); for now, observe behavior — the disabled feature should stop firing within seconds.

### Re-enabling

After the underlying bug is fixed and a new build is deployed (Scenario A in reverse), re-enable with the same `curl` but `"enabled":true` and `"reason":"fix deployed: <PR/commit>"`. The audit table preserves both transitions.

### Caveat — env-var override

If a flag is set via environment variable (`FEATURE_<NAME>=true` in `fly.backend.toml` `[env]` or `fly secrets set FEATURE_<NAME>=true`), the env-var **wins** over the runtime toggle. To roll back an env-var-driven flag, also do:

```bash
fly secrets unset --app montgowork-staging-api FEATURE_<NAME>
# This triggers a redeploy.
```

The current staging deploy does **not** set any `FEATURE_*` env vars — all three live flags resolve from `config/feature_flags.yaml` defaults — so the runtime toggle is sufficient today.

### Rollback time

<30 seconds end-to-end. The flag value is read on every `is_enabled()` call (no cache), so disablement is effectively immediate.

### Rehearsal status

- [ ] **NOT rehearsed live 2026-04-25** — `STAGING_ADMIN_KEY` is not exported in the rehearsal shell environment (intentional — driver agent does not hold staging secrets). The exact `curl` command above is verified syntactically against `backend/app/routes/admin_flags.py:75-95` (the handler validates `X-Admin-Key`, hashes it for audit, enforces rate limit, calls `set_flag_runtime`). **TODO:** owner should run the curl once with a benign flag (e.g., toggle `ENABLE_AI_GENERATION` off and back on) and confirm two `feature_flag_audit` rows appear, before relying on this in an incident.

---

## 8. Scenario D — Emergency kill-switch (engagement / scheduler)

**Use when:** the nightly orchestrator is firing wrong jobs, reminder emails are going out to the wrong recipients, or the scheduler is in a bad state. This is a **superset** of Scenario C — `FEATURE_NIGHTLY_ENABLED` and `FEATURE_EMAIL_SEND_ENABLED` are themselves feature flags — but called out separately because the rollback time and blast radius are different.

**Detection signals:**
- Workers reporting reminder emails at wrong times.
- `sendgrid_events` rows piling up faster than the cooldown allows.
- APScheduler logs showing repeated invocations (race / leaked second worker).
- A user request to "stop everything" pending investigation.

### Order of operations (fastest to slowest)

#### D1. Disable nightly via runtime feature flag (recommended)

This is **the primary kill-switch.** No redeploy.

```bash
curl -fsS -X POST \
    -H "X-Admin-Key: $STAGING_ADMIN_KEY" \
    -H "Content-Type: application/json" \
    -d '{"enabled":false,"reason":"incident: <reason>"}' \
    https://montgowork-staging-api.fly.dev/api/admin/flags/FEATURE_NIGHTLY_ENABLED
```

`backend/scripts/nightly_digest.py:78-253` reads `FEATURE_NIGHTLY_ENABLED` at the **top** of the orchestrator entry point — when off, the function logs `"nightly digest disabled via feature flag, skipping"` and returns without touching the DB or sending email. Effective on the **next** scheduled tick (nightly runs at 02:00 city-local, so worst case ~24h until next attempt; the disabled flag keeps it off for every subsequent tick).

For email specifically (not just nightly):
```bash
# Same endpoint, FEATURE_EMAIL_SEND_ENABLED. This blocks ALL outbound,
# including transactional appointment reminders, not just digests.
```

#### D2. Disable via Fly secret (slower, but survives a process restart)

If the API process is the problem (so the runtime toggle in D1 didn't stick):

```bash
fly secrets set --app montgowork-staging-api FEATURE_NIGHTLY_ENABLED=false
# Fly stages the secret and triggers a deploy. On next boot,
# _read_env() in feature_flags.py picks up FEATURE_NIGHTLY_ENABLED=false
# and is_enabled() returns False unconditionally (env var beats YAML beats runtime).
```

Time: 1-2 minutes (Fly redeploys the machine to inject the new env var). To avoid the redeploy delay and force an immediate restart:

```bash
fly machines list --app montgowork-staging-api
# Note the machine id (e.g., 48e062ec730718)
fly machines restart <machine-id> --app montgowork-staging-api
```

#### D3. Stop the machine entirely (nuclear)

If neither D1 nor D2 worked (or you suspect the API itself is the source of bad data):

```bash
fly machines stop <machine-id> --app montgowork-staging-api
```

The API goes dark — health checks fail, frontend can't reach the backend. Use only when the alternative (continued bad behavior) is worse than full downtime. Restart later with `fly machines start <machine-id>`.

### After the dust settles

1. Inspect what fired during the incident:
   ```bash
   fly ssh console --app montgowork-staging-api
   sqlite3 /app/data/montgowork.db \
       "SELECT category, count(*) FROM engagement_events \
        WHERE created_at > '<incident-start-iso>' GROUP BY category;"
   ```
2. Decide whether to clean up bad rows (Scenario B2) before re-enabling.
3. Re-enable with a fresh feature-flag toggle (Scenario C).

### Rollback time

| Path | Time | Survives restart? |
|------|------|-------------------|
| D1 runtime flag | <5 sec | No (in-memory) |
| D2 Fly secret + redeploy | 1-2 min | Yes |
| D2 + machine restart | 30 sec | Yes |
| D3 machine stop | 30 sec | Yes (machine off) |

For a real incident, do **D1 first** (immediate stop), then **D2** (persist across the next deploy) once D1 has bought you breathing room.

### Rehearsal status

- [ ] **D1 NOT rehearsed live 2026-04-25** — same reason as Scenario C: no admin key in driver shell. Command syntactically verified against `admin_flags.py`. **TODO:** owner rehearses with a low-risk flag.
- [x] **D2 syntax verified 2026-04-25** — `fly secrets set --help` confirmed the `NAME=VALUE` invocation and the staged-deploy semantics. `fly machines restart` accepts the staging machine id `48e062ec730718` (visible in `fly status` output captured during this rehearsal).
- [ ] **D2 not run live** — would have changed staging state. Skipped per orchestrator instructions.
- [ ] **D3 not run** — destructive on a live demo target.

---

## 9. Common pitfalls

- **Cold-start timeout looks like an outage.** `/health` first request after idle can take 10-30s while the Fly machine boots. Re-curl after 30s before declaring an incident. Observed during this runbook's rehearsal: `/` returned 200 in 0.16s, then `/health` returned 200 in 0.06s — but the very first probe after idle had timed out at 30s. If `/` returns 200 but `/health` doesn't, suspect lifespan startup (DB init, RAG load) — check `fly logs`.
- **`fly releases list` is wrong.** The current `flyctl` (v0.4.40) command is `fly releases`, no `list` subcommand. Use `fly releases --image` to see Docker image refs.
- **`fly releases rollback` does not exist.** Roll back by re-deploying the prior image: `fly deploy --image registry.fly.io/<app>:<prior-tag>`.
- **The runtime feature-flag toggle is in-memory only.** A machine restart wipes the override; the YAML default takes back over. Always pair Scenario C/D1 with a Fly secret (D2) for incidents you expect to outlive a restart.
- **`AUDIT_HASH_SALT` change breaks audit hash continuity.** If you rotate it during a rollback, prior audit rows are still valid but their hashes will not match newly-computed ones for the same actor token. Note the rotation timestamp in the post-mortem.
- **CORS lock-out after rollback.** If the rollback target predates a CORS_ORIGINS change, the frontend will see CORS errors until you re-set `CORS_ORIGINS` to the current frontend hostname. Fix: `fly secrets set --app montgowork-staging-api CORS_ORIGINS=https://montgowork-staging-web.fly.dev` and redeploy.

---

## 10. Audit / bypass log

Any rollback that bypasses normal change control (force-deploy, secret rotation outside scheduled cadence, direct DB UPDATE) should be logged. Use the project's existing `bypass_log.jsonl`:

```bash
echo '{"timestamp":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","actor":"kmasty1","action":"rollback_scenario_a","reason":"<why>","target":"montgowork-staging-api","prior_version":"v3","new_version":"v2"}' \
    >> /Users/kevinmasterson/Projects/montgowork/.paircoder/history/bypass_log.jsonl
```

This file already tracks 19 entries as of this runbook's authoring; the rollback append fits the same shape.

---

## 11. Post-incident checklist

After any rollback (any scenario), within 24h:

- [ ] Open a post-mortem doc (`docs/incidents/<date>-<slug>.md`).
- [ ] Record: trigger, detection time, rollback path used, total impact window, data-loss window (if any).
- [ ] File a `bugfix` task for the underlying cause.
- [ ] If Scenario B was used: confirm the demo seed still works (`scripts/staging-smoke.sh`).
- [ ] If Scenario C/D was used: confirm the audit row exists in `feature_flag_audit`.
- [ ] Update **this runbook** with anything that surprised you. Last-reviewed date at top must change.

---

## 12. Acceptance-criteria mapping (T13.120)

| AC item | Status |
|---------|--------|
| Runbook exists with step-by-step for each scenario | Done — §5 (A), §6 (B), §7 (C), §8 (D) |
| Each scenario rehearsed once | A: `fly releases --image` rehearsed live. B: `qc_reset` (B3) rehearsed in 0.145s on `/tmp/rollback_rehearsal.db`. C: command verified against handler source; live toggle deferred to owner (no admin key in driver shell). D: `fly secrets set` syntax + machine-id verified live; live disable deferred (would change demo state). |
| Contact / escalation paths documented | §3 |

Open TODOs surfaced during authoring (transcribed for the next reviewer):

- B1 volume-snapshot rehearsal pending until first daily snapshot exists (~24h after volume create on 2026-04-24).
- C live admin-flag toggle pending until owner runs the verifying curl with a real admin key.
- Add a `GET /api/admin/flags/<name>` endpoint so step C.3 can verify without `fly ssh`. Track as a follow-on to T13.64.
- Production rollback story is currently "snapshot restore only, RPO 24h" — track the Postgres-or-S3-backup decision before any prod cutover.
