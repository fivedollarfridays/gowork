# Sprint S12a --- Worker Companion: Foundation + Daily Loop

**Plan type:** feature
**Sprint:** S12a
**Total Cx:** 520
**Tasks:** 26 (P0: 26)
**Revision:** v3 (2026-04-23) — split from consolidated S12 backlog after second-pass agent review surfaced sprint-size and new-issue blockers.

## Goal

Ship the minimum viable worker-companion daily loop: a worker creates a pathway plan, appointments auto-generate from barriers, worker tracks job applications, stall signals detect inactivity, and a nightly job composes and sends a daily digest email. This sprint establishes the foundational infrastructure (migrations, DB-backed outcomes store, feature flags, scheduler, email) and the end-to-end daily loop with in-app appointments and digest pages. **Does not include** resume/cover-letter generation, plan-refresh on stall, reminder engine with cooldown, transactional appointment emails, advisor inbox — those land in S12b.

Derived from architectural analysis in `ops:/Users/kevinmasterson/ops/lib/{appointment_*,nightly_retro,nightly_day_boundary,nightly_accounting,daily_plan_builder,daily_plan_dedupe,engagement_status,job_tracker,conversion_triggers,cooldown}.py`.

## What ships in S12a vs S12b

**S12a (this sprint):** Migration infra, DB outcomes store, feature flags, schema for all new tables, SendGrid send + event webhook, APScheduler, shared types, appointments CRUD + pathway linker + routes + frontend, jobs lifecycle + funnel + routes, evidence collector, stall detector, digest composer, retro, nightly orchestrator (direct send — no reminder engine yet), daily digest frontend page, E2E tests, intelligence wire-up, integration gate.

**S12b (next sprint, see `backlog-sprint-s12b-value-extensions.md`):** PDF rendering, appointment enrichment, availability engine, transactional emails, signed manage-links, worker voice + resume builder + cover letter, reminder engine with cooldown, full engagement API routes, weekly review, plan refresher, past-appointment auto-advance, module status contracts, jobs kanban, documents pages, nav + stall banner, advisor inbox, demo seed, worker data export / right-to-delete, E2E + gate.

## Architectural principles

- **All files under 400 lines, all functions under 50 lines** (existing mw standard)
- **City-aware throughout** — every new module respects `CITY` env var and reads from `cities/{city}.yaml`
- **Zero hardcoded AL or TX references** — route through existing city config pattern
- **Deterministic where possible** — no LLM in S12a (LLM paths are S12b, gated behind `ENABLE_AI_GENERATION` from T12.0b)
- **N+1 friendly** — every user action writes structured events to the DB-backed outcomes store (T12.0a)
- **Schema-first** — all new tables defined in Phase 1 before any module reads them, regardless of which sprint consumes them
- **No unauthenticated job registration** — APScheduler jobs fire only on cron or `require_admin_key`-protected trigger
- **Event-driven, not import-driven** — modules that emit domain events (T12.7 appointment transitions) use a lightweight in-process pub/sub; consumers subscribe. No module imports a consumer it fires events at.
- **PII conservatism** — new tables containing court dates, cleared-record status, or barrier detail CASCADE DELETE on session expiry; no loose-text session references
- **S12b compliance gate** — worker data export / right-to-delete ships in S12b (T12.36). S12a must NOT go to general availability in a production environment before S12b lands — staging and controlled-beta only.

---

## Phase 0: Prerequisites (must land first)

### T12.0 --- Migration Infrastructure | Cx: 20 | P0

**Description:**
`backend/app/core/migrations/` does not exist. `schema.py` ships as a single `DDL_SQL` blob (`schema.py:3-149`) with no versioning. Create a lightweight migration system following the `ops:lib/db.py` pattern (`_ensure_schema`, `_current_version`, `_apply_migrations` at `db.py:17-95`) with per-migration Python modules (`m001_initial.py`, `m002_s12_worker_companion.py`, …) each exporting `SCHEMA_VERSION = N` and `upgrade(conn)` / `downgrade(conn)` functions.

**AC:**
- [ ] `backend/app/core/migrations/runner.py` with `apply_pending(db_path) -> list[str]`
- [ ] Per-migration module convention matches `ops:lib/migrations/m001_initial.py` shape (Python module, not SQL file)
- [ ] `schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)` tracking table auto-created
- [ ] Existing `DDL_SQL` extracted as `m001_initial.py` with verified byte-for-byte DDL equivalence
- [ ] Forward-only by default; `--rollback <version>` uses the module's `downgrade(conn)` function
- [ ] Dry-run mode prints SQL without executing
- [ ] Tests cover fresh DB, existing DB with zero migrations, re-run idempotency, rollback, schema_migrations integrity
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T12.0a --- DB-Backed Outcomes Store | Cx: 25 | P0

**Description:**
Current `backend/app/modules/outcomes/tracker.py:24-26` is an in-memory dict upsert — `self._records[record.session_id] = record` — which overwrites prior outcomes and loses all state on restart. This breaks the "N+1 friendly" principle and is assumed as an append-only signal sink by T12.7, T12.11, T12.18, T12.22, T12.23. Replace with a SQLite-backed append-only store. Reference patterns: `ops:lib/conversion_tracking.log_conversion` and `ops:lib/block_decisions.record_decision` (both append-only).

**Callers that must be updated in this task** (not a separate compat shim):
- `backend/app/modules/outcomes/aggregator.py:12`
- `backend/app/modules/outcomes/intelligence.py` (existing integration)
- `backend/tests/test_outcome_tracker.py`
- `backend/tests/test_outcome_aggregator.py`
- `backend/tests/test_s8_coverage_gaps.py`

**AC:**
- [ ] New `outcomes_records` table defined in m002 migration (owned by T12.1): `id INTEGER PK, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE, event_type TEXT NOT NULL, payload_json TEXT, created_at TEXT NOT NULL, barriers_cleared_snapshot_json TEXT`
- [ ] `OutcomeTracker(db_path)` constructor accepts DB path; `record_outcome()` INSERTs (never upserts)
- [ ] `list_by_session(session_id) -> list[OutcomeRecord]` returns chronological history
- [ ] `list_recent(city, event_type, since)` for aggregate intelligence queries
- [ ] **All 5 existing callers** (`aggregator.py`, `intelligence.py`, 3 test files) updated to use new constructor signature — listed above, all must pass
- [ ] `get_latest(session_id)` convenience method preserved for existing `intelligence.py` call pattern (documented audit of call sites included in PR)
- [ ] Tests cover: multiple writes per session, process-restart durability, cross-session aggregates, CASCADE on session delete, all 3 updated existing test files pass
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.0, T12.1

---

### T12.0b --- Feature Flag Infrastructure + Audit | Cx: 15 | P0

**Description:**
`ENABLE_AI_GENERATION` (S12b-only), `FEATURE_NIGHTLY_ENABLED` (default **true**), and `FEATURE_EMAIL_SEND_ENABLED` (default **true**) are all load-bearing toggles. Create `backend/app/core/feature_flags.py` with stdlib-only resolution chain (env → yaml → default) and a `require_admin_key`-protected admin endpoint for runtime toggle with structured audit.

**AC:**
- [ ] `is_enabled(flag_name, default=False) -> bool` reads env var `FEATURE_<NAME>`, then `config/feature_flags.yaml`, then default
- [ ] `POST /api/admin/flags/{name}` body: `{enabled: bool, reason: str}` — requires `require_admin_key`
- [ ] **Audit record schema explicit**: `flag_name, old_value, new_value, reason, actor_token_hash (SHA256 of admin token), source_ip, timestamp` — written to new `feature_flag_audit` table in m002 migration
- [ ] **Rate limit**: max 10 toggle ops per admin token per hour (429 on exceed)
- [ ] Enabling `ENABLE_AI_GENERATION` logs an explicit warning line: "AI generation enables LLM processing of worker PII — verify data processing agreement is active"
- [ ] Defaults documented in `.env.example`: `FEATURE_NIGHTLY_ENABLED=true`, `FEATURE_EMAIL_SEND_ENABLED=true`, `ENABLE_AI_GENERATION=false`
- [ ] Tests cover resolution chain, admin toggle, audit write with all required fields, rate-limit 429, AI-generation warning emission
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.0, T12.1

---

## Phase 1: Foundation Infrastructure

### T12.1 --- Database Schema Migrations (All Tables) | Cx: 30 | P0

**Description:**
Create `m002_s12_worker_companion.py` (via T12.0's module convention) adding **all** new tables required across S12a AND S12b — schema-first means every table exists before any module reads it. All `session_id` columns are `TEXT` (matches `sessions.id TEXT PRIMARY KEY` at `schema.py:60`). All session FKs declare `ON DELETE CASCADE`. `plan_history` coexists with existing `sessions.previous_plan` column — dual-write during transition; deprecation of `previous_plan` scheduled for S13.

**Tables created (complete inventory):**

| Table | Purpose | Owner (sprint) |
|---|---|---|
| `appointments` | Worker appointment records | S12a |
| `job_applications` | Job application lifecycle rows | S12a |
| `resume_versions` | Resume + cover letter versions | S12b |
| `daily_progress_snapshots` | Per-day retro results | S12a |
| `engagement_events` | Email sends, bounces, stalls, auto-advances | S12a+S12b |
| `plan_history` | Archived plans from refresh | S12b |
| `outcomes_records` | Append-only outcomes signal store (T12.0a) | S12a |
| `reminder_cooldowns` | Dedup table for reminder engine | S12b |
| `nightly_run_log` | Structured accounting per nightly run | S12a |
| `scheduler_leases` | Multi-worker scheduler lock (if chosen over WEB_CONCURRENCY=1) | S12a |
| `worker_unavailability` | Worker-declared availability blocks | S12b |
| `feature_flag_audit` | T12.0b audit trail | S12a |
| `sendgrid_events` | SendGrid Event Webhook ingestion | S12a |

**AC:**
- [ ] All 13 tables created with correct columns and types
- [ ] All `session_id` columns are `TEXT` — grep assertion in test
- [ ] All session FKs declare `ON DELETE CASCADE`
- [ ] Indexes on frequently-queried columns (`session_id`, `status`, `starts_at`, `applied_date`, `date`, `created_at`)
- [ ] `plan_history` row schema: `id, session_id, archived_at, plan_json, refresh_reason, triggering_event`
- [ ] `plan_history` capped at 20 most recent per session (enforcement in T12.24; migration includes comment)
- [ ] Migration idempotent — running twice produces no changes
- [ ] Downgrade (`m002.downgrade(conn)`) provided; rollback tested round-trip on seeded DB
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.0

---

### T12.2 --- Email Integration (SendGrid Send) | Cx: 20 | P0

**Description:**
Add `backend/app/integrations/email/` module with thin SendGrid wrapper. `send_transactional(to, subject, html, text_fallback, category)`. Retry logic (3 attempts, exponential backoff). Respects `FEATURE_EMAIL_SEND_ENABLED` kill switch. Failed sends logged to `engagement_events`.

**AC:**
- [ ] `send_transactional()` with retry + structured logging
- [ ] Category tagging for digest / reminder / stall-alert / appointment-confirmation / appointment-reminder types
- [ ] Mock provider for tests (no live API calls)
- [ ] Respects `FEATURE_EMAIL_SEND_ENABLED=false` (no-op with audit log)
- [ ] Failed sends logged to `engagement_events` with error detail
- [ ] Pre-send dedup check: skips address if recent hard-bounce event present (populated by T12.2a)
- [ ] `SENDGRID_API_KEY` documented in `.env.example` — **scoped to "Mail Send" only** (no contact list, sender management, or activity read permissions)
- [ ] Runbook at `docs/ops/sendgrid-setup.md` covers sender domain auth (SPF/DKIM) and the scoping restriction
- [ ] Unit tests cover retry/backoff, structured log emission, failure path, kill switch, bounce dedup
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.0b, T12.1

---

### T12.2a --- SendGrid Event Webhook | Cx: 15 | P0

**Description:**
SendGrid sends bounce and spam-complaint notifications to a webhook. Without ingestion, reminders degrade silently in prod and reputation damage accrues. Create `backend/app/routes/sendgrid_webhook.py` to receive `POST /api/webhooks/sendgrid/events` with HMAC-signed payload verification. Writes to `engagement_events(category='bounce'|'spam_report'|'delivered'|'open')` and `sendgrid_events` table. On **hard bounce**, auto-sets `reminders_enabled=False` on the affected session.

**AC:**
- [ ] `POST /api/webhooks/sendgrid/events` verifies SendGrid signature via `SENDGRID_WEBHOOK_PUBLIC_KEY` env var (ECDSA verification per SendGrid spec)
- [ ] Event types handled: `bounce`, `dropped`, `spam_report`, `delivered`, `open`
- [ ] Hard bounce → `sessions.reminders_enabled = False` + audit entry
- [ ] Soft bounce → logged, no auto-action
- [ ] Spam complaint → `sessions.reminders_enabled = False` + advisor flag
- [ ] All events mirrored to `engagement_events` (category) AND `sendgrid_events` (raw payload for audit)
- [ ] Unsigned / malformed payloads return 401 and are logged
- [ ] Tests cover: signature verify happy + fail, each event type, hard-bounce side effect
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.1, T12.2

---

### T12.3 --- APScheduler + Day-Boundary Helpers | Cx: 20 | P0

**Description:**
Add APScheduler to `backend/requirements.txt` and wire into FastAPI lifespan. Create `backend/app/core/scheduler.py` with job registration helpers. Register two recurring jobs for S12a: `nightly_digest` (02:00 city-local daily), `stall_scan` (08:00 daily). (`appointment_reminders` job registered but handler lands in S12b T12.10a.)

**Multi-worker safety:** enforce via `scheduler_leases` table (DB-backed distributed lock, lease held for job duration) OR `WEB_CONCURRENCY=1` hard constraint in `main.py` lifespan — pick one and wire in tests. Port `ops:lib/nightly_day_boundary.py` (`current_work_date`, `resolve_work_date`, `_resolve_rollover_hour`) to `backend/app/core/day_boundary.py`.

**AC:**
- [ ] APScheduler starts with FastAPI lifespan, shuts down cleanly on SIGTERM
- [ ] Two jobs registered with correct cron schedules (plus `appointment_reminders` stub)
- [ ] Job registration helper: `register_job(name, func, trigger)`
- [ ] Timezone-aware (respects city config timezone)
- [ ] Multi-worker duplication prevented: `scheduler_leases` with atomic lease acquisition OR `WEB_CONCURRENCY=1` check that raises at startup if violated
- [ ] `day_boundary.current_work_date(city)` ported and tested across DST boundary + multiple rollover-hour configurations
- [ ] **No HTTP endpoint triggers scheduler jobs directly** — jobs fire only via cron or `require_admin_key`-protected admin trigger
- [ ] Scheduler state logged on startup
- [ ] Tests verify: job registration, multi-worker lock behavior under `WEB_CONCURRENCY=2`, day-boundary helper across DST
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.0

---

### T12.5 --- Shared Schemas + Timezone Helpers | Cx: 15 | P0

**Description:**
Create `backend/app/modules/common/temporal_types.py` with Pydantic models and enums shared across appointments/jobs/engagement: `AppointmentType`, `AppointmentStatus`, `JobApplicationStatus`, `EngagementEventType`, `StallLevel`, `GenerationMethod`. Port `ops:lib/nightly_phases/timezone_utils.py:format_ct` as city-generic `format_city_local(dt, city)`.

**AC:**
- [ ] All shared enums defined with stable string values (tested round-trippable through SQLite TEXT)
- [ ] `GenerationMethod = Enum("llm" | "template")` present (used by S12b)
- [ ] Pydantic models validate timezone awareness
- [ ] `format_city_local(dt, city) -> str` renders in the city's configured timezone
- [ ] No circular imports with existing modules
- [ ] Tests cover enum membership, model validation, formatter across two cities
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

## Phase 2: Appointments Module (core)

### T12.6 --- Appointments Types + Models | Cx: 15 | P0

**Description:**
Create `backend/app/modules/appointments/types.py` with `Appointment` Pydantic model (id, session_id, type, title, starts_at, ends_at, location_name, location_address, barrier_link, status, source, notes).

**AC:**
- [ ] `Appointment` model with all fields and validators
- [ ] `AppointmentType` enum matches barrier types where applicable
- [ ] `barrier_link` optional FK to barrier_id for pathway-sourced appointments
- [ ] JSON-serializable for API responses
- [ ] Tests for model validation edge cases (past dates, zero-duration, missing location)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.1, T12.5

---

### T12.7 --- Appointments CRUD (Event-Emitting) | Cx: 25 | P0

**Description:**
Create `backend/app/modules/appointments/scheduler.py` with pure CRUD: `create()`, `get()`, `list_by_session()`, `list_upcoming()`, `update()`, `mark_attended()`, `mark_missed()`, `cancel()`, `reschedule()`. Status transitions validated (port `ops:lib/job_tracker._check_status` pattern).

**Event-driven coupling (not import-driven):** `mark_attended()` and `mark_missed()` **emit** events via `backend/app/core/events.py` (lightweight in-process pub/sub). Consumers in S12b (transactional emails T12.10a, enrichment T12.7a) subscribe; this module does not import them. Event names: `appointment.created`, `appointment.attended`, `appointment.missed`, `appointment.rescheduled`. For S12a, the only subscriber is T12.0a outcomes store (via an `outcomes_listener` module that subscribes to all appointment events and appends to `outcomes_records`).

**AC:**
- [ ] All CRUD functions implemented with status validation (port `_check_status`)
- [ ] `mark_attended()` and `mark_missed()` emit events (do NOT import consumers); outcomes listener subscribed at app startup
- [ ] `backend/app/core/events.py` event bus: `emit(event_name, payload)`, `subscribe(event_name, handler)`, thread-safe, sync dispatch (async optional follow-up)
- [ ] `reschedule()` preserves history in notes field
- [ ] Conflict detection: warns if new appointment overlaps existing
- [ ] Tests cover happy paths, all invalid transitions, event emission verified (test subscriber records), outcome history durability
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.0a, T12.6

---

### T12.9 --- Pathway → Appointment Auto-Linker + Reconciliation | Cx: 25 | P0

**Description:**
Create `backend/app/modules/appointments/barrier_linker.py`. Hook called from the two route callers (`routes/pathway.py:67`, `routes/plan_intelligence.py:80`) — NOT inside `generate_pathways()` (engine stays pure). Creates appointment placeholders for stages that require scheduled events. Ports `ops:lib/appointment_reconciliation.py` (`find_placeholder_matches`, `validate_patch`).

**AC:**
- [ ] Placeholder generation covers expunction, benefits recert, DMV, childcare intake, court dates
- [ ] City-aware: correct state agency names (HHSC vs DHR)
- [ ] Idempotent — reconciles against existing
- [ ] Hook inserted at BOTH `routes/pathway.py` AND `routes/plan_intelligence.py` — test exercises both callers
- [ ] `generate_pathways()` signature unchanged — remains session-agnostic and pure
- [ ] `find_placeholder_matches(new_appointment)` returns candidate merge targets; `validate_patch` validates patch shape
- [ ] Tests verify AL + TX placeholder content, idempotency, reconciliation on manual-create-matches-placeholder
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.7

---

### T12.10 --- Appointments API Routes | Cx: 15 | P0

**Description:**
Create `backend/app/routes/appointments.py` with nine endpoints: `GET /api/appointments?session_id=X`, `POST /api/appointments`, `GET /api/appointments/{id}`, `PATCH /api/appointments/{id}`, `DELETE /api/appointments/{id}`, `POST /api/appointments/{id}/attended`, `POST /api/appointments/{id}/missed`, `GET /api/appointments/upcoming?session_id=X&days=7`, `POST /api/appointments/from-pathway?session_id=X`.

**AC:**
- [ ] All nine endpoints implemented with proper HTTP codes
- [ ] Input validation via Pydantic
- [ ] Session ownership check (no cross-session reads)
- [ ] Routes registered in `all_routers` and tested for registration
- [ ] Tests cover happy path + auth + malformed input per endpoint
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.7, T12.9

---

## Phase 3: Job Application Tracker

### T12.11 --- Job Applications Lifecycle | Cx: 20 | P0

**Description:**
Create `backend/app/modules/jobs/applications.py`. Full lifecycle: `create(session_id, job_match_ref, company, role, resume_version_id)`, `update_status(id, new_status, outcome_date=None)`, `list_by_session()`, `list_by_status()`. Emits events (via T12.7 event bus) on status transitions: `job_application.created`, `.applied`, `.interview`, `.offer`, `.rejected`, `.withdrawn`. Outcomes listener appends to `outcomes_records`.

**Matching linkage:** `matching.JobMatch` (`types.py:174-188`) has no `id` field. Link via composite `(source, url)`. Both fields are Optional — if either is None, raise; composite cannot be partial.

**AC:**
- [ ] Full lifecycle with validated transitions (port `job_tracker._check_status`)
- [ ] Each transition emits event (outcomes listener appends to `outcomes_records` with cleared_barriers snapshot)
- [ ] Linking to job match via composite `(source, url)` — **both non-null required, composite violation raises ValueError** (documented in module header)
- [ ] Linking to `resume_versions` table prepared (FK to table that lands in S12b)
- [ ] Tests cover every status transition, invalid transitions, None-composite guard, outcome history durability
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.0a, T12.1, T12.5, T12.7 (for event bus)

---

### T12.12 --- Jobs Funnel Analytics (with k-anonymity) | Cx: 20 | P0

**Description:**
*Elevated from P1 in v2 — T12.33 intelligence wire-up (P0) depends on this.*

Create `backend/app/modules/jobs/funnel_analytics.py`. Per-session: `compute_funnel(session_id)`. Aggregate (city-scoped): `compute_community_funnel(city, segment_by=None)`. Feeds `outcomes/intelligence.py`.

**k-anonymity:** Suppress any segment cell with fewer than 5 sessions. Return `null` count + `suppressed: true` flag — prevents re-identification in small cities.

**AC:**
- [ ] Per-session funnel returns structured dict (draft/applied/interview/offer counts + conversion rates)
- [ ] Community funnel segments correctly by `cleared_barriers`, `fair_chance_employer`, `industry`
- [ ] **Cells with < 5 sessions return `null` with `suppressed: true`** — not the count
- [ ] `outcomes/intelligence.py` imports + exposes `application_conversion_rates` in `/api/intelligence/barriers` response — additive only, no shape break
- [ ] Demo sessions (tagged `demo=true` — S12b T12.34) excluded from aggregates (guard added now so S12b seed doesn't leak)
- [ ] Tests cover empty DB, single session, single-cell suppression, multi-session above threshold
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.11

---

### T12.13 --- Jobs API Routes | Cx: 15 | P0

**Description:**
Create `backend/app/routes/jobs_applications.py`. **Route prefix: `/api/job-applications`** — NOT `/api/jobs` (collision with existing `routes/jobs.py:13` which owns `/api/jobs/{job_id}`). Endpoints: `GET`, `POST`, `PATCH /{id}`, `GET /funnel?session_id=X`, `GET /community-funnel?segment_by=X`.

**AC:**
- [ ] All five endpoints under `/api/job-applications` prefix
- [ ] No collision with `/api/jobs/{job_id}` — integration test hits both and asserts distinct handlers (shape check)
- [ ] Community funnel respects city scoping AND T12.12 k-anonymity suppression
- [ ] Routes registered and tested
- [ ] Tests cover auth + happy path + malformed input + route-resolution correctness
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.11, T12.12

---

## Phase 4: Evidence + Stall + Retro

### T12.23 --- Evidence Collector | Cx: 15 | P0

**Description:**
Create `backend/app/modules/plan/evidence_collector.py`. `collect_evidence(session_id, date_range)` returns unified `EvidenceBundle` (checklist_items_completed, appointments_attended, appointments_missed, applications_filed, applications_progressed, outcomes_logged). **Moved ahead of T12.22 retro and T12.20 digest which both depend on it.**

**AC:**
- [ ] Unified evidence bundle with all six signal types
- [ ] Date-range inclusive on both ends
- [ ] City-scoped (no cross-city)
- [ ] Reads from DB-backed outcomes store (T12.0a) for historical events
- [ ] Tests cover overlapping ranges, empty range, single-day, multi-session isolation
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.0a, T12.7, T12.11

---

### T12.18 --- Stall Detector | Cx: 25 | P0

**Description:**
Create `backend/app/modules/engagement/stall_detector.py`. `scan_active_sessions()` computes `days_since_last_progress` per session. Returns `StalledSession(session_id, stalled_barriers, days_stalled, stall_level)`. SOFT (≥3d), MEDIUM (≥7d), HARD (≥14d). Port `ops:lib/engagement_status.py` (`get_engagement_status`, `_get_recommendations`).

**Note on S12a scope:** T12.18 detects and classifies. Does NOT send reminders — that's T12.19 (S12b). Stall info surfaces in the digest (T12.20).

**Auto-advanced appointments (S12b T12.25a) suppression:** Auto-missed appointments within a 48h suppression window do NOT count as a stall signal. (Prevents false-positive stalls from late-entered attended status.) This AC locks in the contract; S12a enforcement is that `outcomes_records` with `event_type='appointment_auto_advance'` are filtered out of stall computation regardless of whether T12.25a exists yet.

**AC:**
- [ ] Stall detection considers four progress signals (reads from T12.23 evidence collector)
- [ ] Levels correctly assigned by day thresholds
- [ ] Per-barrier stall tracking (not just session-level)
- [ ] `get_engagement_status(session_id)` returns enriched struct with `_get_recommendations` output
- [ ] **Auto-advance suppression**: outcomes with `event_type='appointment_auto_advance'` within last 48h filtered from stall signal
- [ ] Idempotent: running twice same day produces same result
- [ ] Tests cover all stall levels + no-stall case + multi-barrier mixed stalls + auto-advance suppression
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.23

---

### T12.22 --- Daily Progress Module (Retro) | Cx: 20 | P0

**Description:**
Create `backend/app/modules/plan/daily_progress.py`. `run_nightly_retro(session_id, for_date)` compares plan's expected actions vs actual evidence (from T12.23). Port `ops:lib/nightly_retro.py` (`collect`, `persist`, `load`, `collect_for_date`, `_derive_done_flags`, `RetroResult`).

**AC:**
- [ ] Retro runs for a single session + date and returns structured result
- [ ] Evidence sourced from T12.23 (NOT re-implementing signal collection)
- [ ] Classification handles done/undone/partial
- [ ] Snapshot persisted to `daily_progress_snapshots`
- [ ] Tests cover no-evidence, full-evidence, mixed cases
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.23

---

## Phase 5: Digest Composer + Orchestrator

### T12.20 --- Digest Composer | Cx: 30 | P0

**Description:**
Create `backend/app/modules/engagement/digest_composer.py`. `compose_digest(session_id, for_date)` builds structured daily email: yesterday (attended appointments, filed applications, cleared barriers), today (upcoming appointments, scheduled actions), this-week (newly listed fair-chance jobs, upcoming recert windows), stall alerts.

**Port additions:**
- `ops:lib/daily_plan_builder.carry_forward_blocks` + `_schedule_title_stale` (named helper) — roll forward undone actions with stale detection
- `ops:lib/daily_plan_dedupe.dedupe_by_time_slot`
- `ops:lib/nightly_phases/_notify_carryover.render_carryover`
- `ops:lib/nightly_phases/_notify_upcoming.render_upcoming_appointments`

Worker first name sourced from `sessions.profile` JSON field (documented — no `first_name` column exists).

**AC:**
- [ ] All four sections with correct data; empty sections omitted
- [ ] Yesterday-undone items carried forward with stale-detection (`_schedule_title_stale` named explicitly)
- [ ] Time-slot dedup applied
- [ ] Personalization: worker first name from `sessions.profile` JSON (source documented), city-appropriate agency names
- [ ] **All worker-supplied dynamic values HTML-escaped** — test with name containing `<` asserts output contains `&lt;`
- [ ] HTML + plain text both generated
- [ ] Snapshot tests for all-empty and all-populated cases
- [ ] Tests cover empty-signal, fully-populated, mixed, carryover tiers
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.10, T12.13, T12.18, T12.23

---

### T12.21a --- Digest Preview Endpoint | Cx: 5 | P0

**Description:**
Minimal slice of T12.21 (engagement API routes) required for frontend T12.29. Single endpoint: `GET /api/engagement/preview-digest?session_id=X` — renders today's digest via T12.20 without sending. Remaining four engagement endpoints land in S12b T12.21.

**AC:**
- [ ] `GET /api/engagement/preview-digest?session_id=X` returns both html + text variants
- [ ] Session ownership check
- [ ] Uses T12.20 compose_digest; does NOT send
- [ ] Registered in `all_routers`
- [ ] Tests cover authenticated session, unauthorized cross-session, empty-state digest
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.20

---

### T12.25 --- Nightly Orchestrator + Accounting (S12a scope) | Cx: 25 | P0

**Description:**
Create `backend/scripts/nightly_digest.py` as the APScheduler job handler. Runs at 02:00 city-local (via T12.3 day-boundary helper). **S12a scope** — plan-refresh (T12.24) and reminder-engine-with-cooldown (T12.19) land in S12b. For each active session: (1) run retro for yesterday, (2) check stall signals, (3) compose digest for today, (4) send via T12.2 SendGrid directly (reminder engine replaces this call in S12b).

Port `ops:lib/nightly_accounting.py` (`build_accounting_record`, `save_session`, `load_session`) — structured record per run to `nightly_run_log`.

**City scope:** orchestrator filters sessions by `city` parameter. Default invocation iterates cities sequentially — each city's sessions are processed in a city-scoped batch. **Does not** process all-sessions cross-city in one call. Audit trail in `nightly_run_log` includes `city` column.

**AC:**
- [ ] Script iterates active sessions per-city, with `asyncio.Semaphore(10)` bound within each city
- [ ] City scope enforced: sessions from City A never processed in a City B orchestrator invocation (test asserts)
- [ ] Errors in one session don't abort the batch (per-session try/except with structured error log)
- [ ] Structured accounting record written to `nightly_run_log` per run: `city, sessions_processed, emails_sent, errors, duration_sec, start_ts, end_ts`
- [ ] Handles empty-session-pool gracefully
- [ ] APScheduler job correctly registered and triggered by test harness
- [ ] Respects `FEATURE_NIGHTLY_ENABLED` feature flag (kill-switch)
- [ ] Plan-refresh step stubbed out with TODO pointing to S12b T12.24
- [ ] Direct SendGrid send via T12.2 (no reminder engine in S12a); TODO for S12b T12.19 replacement
- [ ] Tests cover empty pool, single session success, multi-session with one failure, kill-switch, city-scope isolation
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.2, T12.3, T12.20, T12.22

---

## Phase 6: Frontend (P0 only)

### T12.26 --- Appointments Page | Cx: 30 | P0

**Description:**
Create `frontend/src/app/appointments/page.tsx` with calendar (month view) + list (upcoming). Create/edit modal. Status transitions via buttons. **Calendar library: `react-big-calendar`** (~50KB bundle). Components: `AppointmentCalendar.tsx`, `AppointmentCard.tsx`, `AppointmentEditModal.tsx`, `PlaceholderPrompt.tsx`.

**AC:**
- [ ] Calendar view (react-big-calendar) + list view shows upcoming 30 days
- [ ] Create/edit/cancel/reschedule all working
- [ ] Placeholder prompts workers to fill in dates
- [ ] All user-visible strings in `locales/en.json` + `locales/es.json`; ESLint blocks hardcoded strings in `.tsx`
- [ ] a11y: ARIA labels, keyboard navigation (axe-core test run)
- [ ] Tests cover all views + CRUD flows
- [ ] Page under 400 lines; components each under 200 lines

**Depends on:** T12.10

---

### T12.29 --- Daily Digest Page | Cx: 20 | P0

**Description:**
Create `frontend/src/app/daily/page.tsx` showing today's digest rendered in-app. Components: `DigestYesterdaySection.tsx`, `DigestTodaySection.tsx`, `DigestWeekSection.tsx`, `StallAlert.tsx`.

**Home redirect contract:** `frontend/src/app/page.tsx` detects session via existing `useSession` hook. If session exists AND not mid-assessment (`assessment_complete=true`), redirect to `/daily`. Unauthenticated or mid-assessment users see current home. Returning users can always reach Assess via nav (T12.30 adds link — not required in S12a since T12.30 is S12b; acceptable gap since nav to Assess exists on current home).

**AC:**
- [ ] Page renders full digest using T12.21a preview endpoint
- [ ] `/` redirects to `/daily` when session exists AND `assessment_complete=true`; unauthenticated + mid-assessment users unaffected
- [ ] Sections collapse/expand
- [ ] Stall alerts clickable → relevant barrier deep-link
- [ ] All strings in locale files; a11y checks
- [ ] Tests cover all section states (populated, empty) + redirect behavior (3 cases: unauth → stay, mid-assessment → stay, post-assessment → /daily)

**Depends on:** T12.21a

---

## Phase 7: Integration + Gate

### T12.32 --- E2E Integration Tests | Cx: 25 | P0

**Description:**
Create `backend/tests/test_s12a_worker_companion_e2e.py`. Full flow tests for S12a scope:

1. Create session + plan → verify pathway placeholders generated → fill in appointment date → mark attended → verify outcome recorded → verify barrier progress
2. Stall scenario: create plan, no activity 4 days → run stall scan → verify SOFT level assigned and surfaced in digest
3. Full nightly digest cycle: activity logged → retro runs → digest composed → email sent via direct SendGrid
4. Test both AL and TX cities

**AC:**
- [ ] Four E2E flows pass for both cities
- [ ] Mocked email sends verified for content + recipient
- [ ] **Route-collision assertion**: test POSTs `/api/job-applications` and asserts response shape differs from `/api/jobs/{id}`
- [ ] **Two-caller pathway hook**: placeholder generation via BOTH `routes/pathway.py` AND `routes/plan_intelligence.py`
- [ ] **k-anonymity**: community funnel test with single-session segment asserts `suppressed: true`
- [ ] **Auto-advance suppression on stall**: inject `appointment_auto_advance` outcome and assert stall detector filters it within 48h window
- [ ] **City-scope on orchestrator**: seed sessions in 2 cities, invoke orchestrator for city A, assert city B sessions untouched
- [ ] **Event emission contract**: test subscriber registered on `appointment.attended` verifies event fired with expected payload
- [ ] No test pollution (clean DB between tests)
- [ ] Runs in under 60 seconds
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.25, T12.26, T12.29

---

### T12.33 --- Intelligence Engine Wire-Up | Cx: 10 | P0

**Description:**
Modify `backend/app/modules/outcomes/intelligence.py` to include `application_conversion_rates` from T12.12. Additive response shape only — S11 capstone consumer verified to tolerate unknown fields.

**AC:**
- [ ] Intelligence endpoint includes `application_conversion_rates` segment
- [ ] Suppressed cells from T12.12 k-anonymity flow through as `null` + `suppressed: true`
- [ ] No breaking changes to existing S11 consumer (regression test on case-manager/community-insights view)
- [ ] New wire-up tests passing
- [ ] `bpsai-pair arch check` passes

**Depends on:** T12.12

---

### T12.35 --- Integration Gate (S12a) | Cx: 20 | P0

**Description:**
S12a final gate. Verifies all foundational infrastructure is solid before S12b builds on it.

**AC:**
- [ ] Full test suite passes (backend + frontend)
- [ ] Zero regressions in existing 2,100+ backend / 800+ frontend tests
- [ ] All new S12a routes respond correctly on fresh deploy (no `/api/jobs` collision)
- [ ] APScheduler jobs fire on test schedule under `WEB_CONCURRENCY=2` — duplicate fire prevented (tests lock/constraint from T12.3)
- [ ] T12.0 migration rollback round-trip tested on seeded DB: migrate up, seed, migrate down, migrate up — integrity preserved
- [ ] **Load test**: nightly orchestrator completes <10min with 200 seeded sessions across 2 cities
- [ ] Two-caller pathway hook verified (both `routes/pathway.py` and `routes/plan_intelligence.py` trigger placeholders)
- [ ] Manual browser walk-through: new session → plan → appointments → application → retro → digest
- [ ] `bpsai-pair arch check` passes across all S12a files
- [ ] **Broad admin-key scan**: grep new route files for any string literal assignment to variables matching `.*(key|secret|token|password).*` — zero hits required
- [ ] **Feature-flag defaults audit**: `ENABLE_AI_GENERATION=false`, `FEATURE_NIGHTLY_ENABLED=true`, `FEATURE_EMAIL_SEND_ENABLED=true` — asserted at startup
- [ ] **All 13 tables present** after m002 migration — integrity check against T12.1 inventory
- [ ] **OutcomeTracker compat**: existing test files (`test_outcome_tracker.py`, `test_outcome_aggregator.py`, `test_s8_coverage_gaps.py`) all pass
- [ ] Runbook at `docs/ops/s12a-rollout.md` documents feature flag enablement order, SendGrid sender verification + webhook setup, 02:00 nightly failure response, and **migration rollback procedure** (including state-undo for in-flight data)
- [ ] Runbook documents **S12a staging-only constraint** — no production general availability until S12b T12.36 (data export / right-to-delete) lands
- [ ] PR description documents feature flags required for prod rollout

**Depends on:** T12.26, T12.29, T12.32, T12.33

---

## Summary by Phase

| Phase | Tasks | Cx | Focus |
|---|---|---|---|
| 0 Prereqs | T12.0, T12.0a, T12.0b | 60 | Migration infra, outcomes DB, feature flags |
| 1 Foundation | T12.1, T12.2, T12.2a, T12.3, T12.5 | 100 | Schema (all tables), email, webhook, scheduler, shared types |
| 2 Appointments | T12.6, T12.7, T12.9, T12.10 | 80 | Types, event-emitting CRUD, linker, routes |
| 3 Jobs | T12.11, T12.12, T12.13 | 55 | Lifecycle, funnel + k-anon, routes |
| 4 Evidence/Stall/Retro | T12.23, T12.18, T12.22 | 60 | Evidence collector, stall detector, retro |
| 5 Digest/Orchestrator | T12.20, T12.21a, T12.25 | 60 | Digest compose, preview endpoint, nightly orchestrator |
| 6 Frontend | T12.26, T12.29 | 50 | Appointments page, daily digest page |
| 7 Gate | T12.32, T12.33, T12.35 | 55 | E2E tests, intelligence wire-up, integration gate |
| **Total** | **26 tasks** | **520 Cx** | |

## New Files (S12a-owned)

- `backend/app/core/migrations/` (runner + m001 + m002)
- `backend/app/core/feature_flags.py`
- `backend/app/core/scheduler.py`
- `backend/app/core/day_boundary.py`
- `backend/app/core/events.py` (in-process pub/sub)
- `backend/app/integrations/email/` (SendGrid send + webhook handler)
- `backend/app/modules/common/temporal_types.py`
- `backend/app/modules/appointments/` (types, scheduler, barrier_linker)
- `backend/app/modules/jobs/` (applications, funnel_analytics)
- `backend/app/modules/engagement/` (stall_detector, digest_composer)
- `backend/app/modules/plan/` (daily_progress, evidence_collector)
- `backend/app/modules/outcomes/tracker.py` (rewritten — DB-backed)
- `backend/app/routes/appointments.py`
- `backend/app/routes/jobs_applications.py`
- `backend/app/routes/engagement_preview.py` (T12.21a)
- `backend/app/routes/sendgrid_webhook.py`
- `backend/scripts/nightly_digest.py`
- `frontend/src/app/appointments/page.tsx`
- `frontend/src/app/daily/page.tsx`

## Cross-Sprint Dependencies

- Builds on **S2** (Fort Worth data) + **S7** (outcome intelligence) + **S11** (Ren's community insights)
- **S12a blocks S12b** — S12b tasks depend on S12a's migration infra, event bus, outcomes store, and scheduler
- **S12a must NOT ship to production GA** before S12b T12.36 (worker data export / right-to-delete) lands — compliance gate. Staging and controlled beta are fine.
- **S13 follow-up**: deprecate `sessions.previous_plan` column in favor of `plan_history` (S12b T12.24 dual-writes during transition)
- No external contract changes for existing endpoints — `/api/intelligence/barriers` adds a field only
- New env vars: `SENDGRID_API_KEY` (Mail-Send scope), `SENDGRID_WEBHOOK_PUBLIC_KEY`, `FEATURE_NIGHTLY_ENABLED=true`, `FEATURE_EMAIL_SEND_ENABLED=true`, `ENABLE_AI_GENERATION=false`
- New backend deps: `apscheduler`, `sendgrid`
- New frontend deps: `react-big-calendar`
- Deployment constraints: `WEB_CONCURRENCY=1` OR scheduler lock honored (T12.3)

## Risks + Mitigations

| Risk | Mitigation |
|---|---|
| Migration infra doesn't exist yet | T12.0 lands first, tested round-trip before any Phase 1 task |
| OutcomeTracker constructor break cascades to existing tests | T12.0a AC names all 5 callers explicitly; driver must update them in the same PR |
| APScheduler multi-worker duplication | `scheduler_leases` lock OR enforced `WEB_CONCURRENCY=1` — T12.3 picks one, T12.35 gate verifies under `WEB_CONCURRENCY=2` |
| SendGrid deliverability degrades silently | T12.2a webhook ingests bounces + spam; hard bounce auto-disables reminders |
| k-anonymity failure on community funnel | T12.12 suppress cells <5 sessions; tested at unit, route, and E2E levels |
| City-scope leak in nightly orchestrator | T12.25 filters by city; T12.32 E2E asserts cross-city isolation |
| Event bus over-imports creating coupling | T12.7 event bus pattern + outcomes listener — no module imports its consumers |
| S12a shipping to prod without delete/export path | Staging-only constraint documented in T12.35 runbook; S12b T12.36 gates GA |
| Plan-refresh and reminder-engine missing in S12a | Explicit stub + TODO in T12.25 pointing to S12b T12.24/T12.19; digest still surfaces stall info |

## Post-S12a Opportunities (land in S12b)

See `backlog-sprint-s12b-value-extensions.md`. Highlights:
- PDF rendering, resume + cover letter builders (LLM-gated)
- Reminder engine with cooldown dedup
- Plan refresher with progress carry-forward
- Transactional appointment emails + signed manage-links
- Weekly review, past-appointment auto-advance, module status contracts
- Jobs kanban, documents pages, advisor inbox
- Worker data export / right-to-delete (compliance gate for GA)
