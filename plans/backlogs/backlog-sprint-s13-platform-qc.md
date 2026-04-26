# Sprint S13 --- Platform-Wide QC + Submission Readiness

**Plan type:** chore
**Sprint:** S13
**Total Cx:** 1,452 (active) — 1,545 inc. cancelled
**Tasks:** 121 active + 7 cancelled (P0: 27, P1: 64, P2: 30)
**Revision:** v2 (2026-04-25) — hackathon-only scope; cancelled post-launch ops items

## Goal

Round out the platform before external submission by building QC infrastructure from scratch (zero `.qc.yaml` suites exist today), authoring browser-driven QC suites covering every user journey in both cities, extending backend integration tests to every module, running exploratory/security/cross-module audits, and closing submission-readiness gaps (staging, error tracking, legal pages, monitoring, rollback plan).

**Prerequisite:** S12b merged (#63). All features exist; this sprint verifies and hardens them.

## What ships in S13 vs deferred

**S13 (this sprint):** QC infrastructure (config + suite dir + template + reset CLI + fake-clock + screenshot baseline + Lighthouse CI + run dashboard), 43 Tier-1 browser suites, 18 Tier-2 backend e2e tests, 7 exploratory agent sweeps, 15 cross-cutting quality gates (i18n/a11y/visual/cross-browser/perf), 12 security+compliance audit items, 6 cross-module integrity checks, 13 submission-readiness items, 4 continuous-QC wiring items.

**Deferred to S14+:** Engineering cleanup items carried from S12b (APP_HOST helper, shared builder free-text helpers, token-system unification, advisor-audit schema consolidation, rate-limiter consolidation, unsubscribe double-connection collapse); any net-new feature work.

## Architectural principles

- **Zero new product features.** Every task either verifies, measures, or polishes existing behavior. Fixes surface as sub-tasks under the failing QC task.
- **Deterministic where possible.** QC suites must be replayable: seeded demo data, fake clock for time-dependent flows, no reliance on wall-clock or external rate limits.
- **Single oracle for pass/fail.** A suite either asserts an observable outcome or it's not a suite. No "looks fine" steps.
- **Fix-forward, no QC-only hacks.** A failing suite means the code changes, not the suite (unless the suite was wrong).
- **Security is a blocking tier.** Any P0/P1 laverna finding blocks submission; P2 may ship with documented risk acceptance.

## Decisions locked (2026-04-24)

1. **Staging env**: stand up before submission. T13.128 added; T13.119 + T13.124 unblocked.
2. **Submission audience**: judges AND prod rollout. Full submission readiness in scope (legal, monitoring, backup, on-call). T13.123 required (not "if applicable").
3. **Error tracking**: Sentry (or equivalent) wired now. T13.121 P1 → in scope.
4. **Visual regression**: in scope. T13.6 + T13.83 in scope.
5. **Headless CI QC**: both — divona-driven manual + Playwright headless in CI. T13.129 added (Playwright harness); T13.125 unblocked.
6. **WCAG target**: AAA. T13.79–T13.82 acceptance criteria escalated.
7. **Legal pages**: author fresh (no templates / attribution). T13.115 scope is full authorship.

---

## Phase 1: QC Infrastructure

### T13.1 --- QC Config + Suite Directory + Authoring Template | Cx: 20 | P0

**Description:**
Create `.paircoder/qc/config.yaml` with environment profiles (`dev` → localhost; `staging` placeholder). Create `.paircoder/qc/suites/` directory. Write `.paircoder/qc/suites/_template.qc.yaml` documenting the schema (name, environment, setup, steps, assertions, cleanup). Write `.paircoder/qc/suites/README.md` with authoring conventions (naming, seeded data requirements, cleanup contract, how to run via divona).

**AC:**
- [ ] `.paircoder/qc/config.yaml` exists with at least `dev` profile pointing at `http://localhost:3000` (frontend) and `http://localhost:8000` (backend)
- [ ] `.paircoder/qc/suites/_template.qc.yaml` documents every required field with comments
- [ ] `.paircoder/qc/suites/README.md` covers: suite naming, demo-session requirements, cleanup contract, how to invoke via divona, what a "step" vs "assertion" is
- [ ] Divona agent can load the template without error (smoke run)
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T13.2 --- Demo Seed Extension (compliance, weekly review, advisor, reminders) | Cx: 20 | P0

**Description:**
Current `demo_seed_s12b.py` covers appointments, jobs, resumes, outcomes, stall states. Extend to seed: compliance-relevant session data (feedback tokens, audit rows pre-state), weekly review data (7-day engagement windows per session), advisor inbox data (case-manager sessions + city scoping), reminder events + cooldown state, engagement preferences in varied states. Every QC suite should be able to find a demo session that exercises its target module.

**AC:**
- [ ] Each of the 10 demo sessions carries state for every module required by any QC suite
- [ ] Seed is deterministic (same row IDs/content on every run given fresh DB)
- [ ] Seed is idempotent (re-running doesn't duplicate rows)
- [ ] A coverage assertion: for every module status key, at least one demo session exposes non-null state
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T13.3 --- QC Reset CLI | Cx: 15 | P0

**Description:**
`scripts/qc_reset.py` (or `bpsai-pair qc reset`) wipes demo-flagged rows across every table and reseeds via T13.2's factory. Must run in under 5 seconds so suites can reset between runs without pain.

**AC:**
- [ ] `python scripts/qc_reset.py` truncates every `demo=1` scoped row
- [ ] Reseeds via T13.2 factory
- [ ] Idempotent: second run is a no-op (or re-deterministic)
- [ ] Does NOT touch non-demo data (assertion tested with a non-demo row sentinel)
- [ ] Runs in <5s on local dev
- [ ] `bpsai-pair arch check` passes

**Depends on:** T13.2

---

### T13.4 --- axe-core Proper Install | Cx: 5 | P1

**Description:**
`axe-core` is imported in `frontend/tests/appointments.test.tsx` but not a declared dep in `frontend/package.json`. Add `@axe-core/react` (or equivalent) to devDependencies, regenerate lockfile, verify it loads cleanly.

**AC:**
- [ ] `@axe-core/react` (or appropriate package) added to `frontend/package.json` devDependencies
- [ ] `package-lock.json` regenerated and committed
- [ ] Existing test that imports axe-core still passes
- [ ] `npm audit` clean

**Depends on:** none

---

### T13.5 --- Fake-Clock Harness for Time-Dependent Tests | Cx: 15 | P1

**Description:**
Scheduled jobs, token TTLs, cooldowns, stall detection, and weekly-review windows are all wall-clock dependent. Build a `backend/tests/_fake_clock.py` fixture that monkeypatches `datetime.now(tz)` project-wide + APScheduler's clock for deterministic test runs. Document usage in a short README.

**AC:**
- [ ] `freeze_time(iso_str)` context manager monkeypatches every `datetime.now` call site
- [ ] `advance_time(seconds)` advances the fake clock and fires any scheduled jobs that would have triggered
- [ ] APScheduler tests can assert "after 23:59 on Sunday, weekly review triggers"
- [ ] One existing flaky time-dependent test migrates to the harness and demonstrates stability
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T13.6 --- Screenshot Diff Baseline Infrastructure | Cx: 20 | P1

**Description:**
Choose a visual-regression approach (recommend: Playwright page.screenshot + pixelmatch, or Percy if we want cloud). Build baseline storage at `.paircoder/qc/baselines/`, a diff helper, and integration into the QC suite runner so suites can add a `screenshot` assertion step.

**AC:**
- [ ] Tool selected and documented in ADR `docs/adr/qc-visual-regression.md`
- [ ] `.paircoder/qc/baselines/` directory populated with at least one reference screenshot
- [ ] Diff helper reports pass/fail with a threshold (e.g., <0.1% pixel diff)
- [ ] One sample suite demonstrates a screenshot assertion
- [ ] `bpsai-pair arch check` passes

**Depends on:** T13.1

---

### T13.7 --- Lighthouse CI Wiring | Cx: 15 | P2

**Description:**
Add `@lhci/cli` to frontend devDependencies, add a `lighthouserc.json` targeting the critical routes, wire a GitHub Action job that runs Lighthouse on every PR and posts a summary comment. Fail the job on score regressions beyond a configurable floor.

**AC:**
- [ ] `lighthouserc.json` covers: `/`, `/daily`, `/appointments`, `/documents`, `/jobs`, `/advisor`
- [ ] CI job runs Lighthouse against a built dev server
- [ ] Score floors: Perf ≥80, A11y ≥90, Best Practices ≥90, SEO ≥90 (tuneable)
- [ ] Regression below floor fails the job
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T13.8 --- QC Run Dashboard | Cx: 20 | P2

**Description:**
A simple static-site dashboard (can be a Next.js page under `/admin/qc` gated by admin key, or a separate `qc-dashboard/index.html`) showing pass/fail for every suite, last-run timestamp, flake indicator, failure trend. Reads from `.paircoder/qc/runs/*.json` output.

**AC:**
- [ ] Every divona suite run writes a JSON result to `.paircoder/qc/runs/`
- [ ] Dashboard page renders latest run per suite
- [ ] Shows flakes (same suite passed+failed in last 5 runs)
- [ ] Shows trend (last 7 days pass rate)
- [ ] `bpsai-pair arch check` passes

**Depends on:** T13.1

---

## Phase 2: Tier 1 Browser QC Suites --- Worker Journeys

### T13.10 --- Suite: Worker Onboarding + Barrier Intake | Cx: 10 | P0

**Description:**
Author `worker-onboarding.qc.yaml`. Covers: first-time user lands → profile creation → initial barrier intake flow → submit → land on plan.

**AC:**
- [ ] Suite runs on both Montgomery and Fort Worth demo sessions
- [ ] Asserts: profile row created, at least one barrier row created, plan generated
- [ ] Runs in ≤60s on local
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.11 --- Suite: Daily Loop (Login → Digest → Actions → Check-in) | Cx: 10 | P0

**Description:**
`worker-daily-loop.qc.yaml`. Login → daily digest page loads → today's actions render → mark an action complete → verify state persists on reload.

**AC:**
- [ ] Digest page renders with at least one action
- [ ] Action completion persists (reload retains state)
- [ ] Outcomes row written
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.12 --- Suite: Plan View + Checklist + History | Cx: 10 | P1

**Description:**
`worker-plan-view.qc.yaml`. Plan page → checklist items render → status update → plan history renders prior plan (if exists).

**AC:**
- [ ] Current plan renders
- [ ] Status update persists
- [ ] Plan history section renders (tests both empty and populated states via different demo sessions)
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.13 --- Suite: Plan Refresher Stall-Trigger Flow | Cx: 15 | P1

**Description:**
`worker-plan-refresh.qc.yaml`. Stall state demo session → advance fake clock past threshold → run nightly orchestrator → verify new plan issued + carry-forward visible + plan_history row capped.

**AC:**
- [ ] Fake clock advances past stall threshold
- [ ] Orchestrator run triggered via CLI or API
- [ ] New plan replaces current; prior plan in history
- [ ] Carry-forward items (same phase/category/title triple) retained
- [ ] plan_history row count ≤ 20
- [ ] Green on both cities

**Depends on:** T13.1, T13.2, T13.5

---

### T13.14 --- Suite: Community Insights "People Like You" | Cx: 8 | P1

**Description:**
`worker-community-insights.qc.yaml`. Render the insights panel → verify city-scoped data → assert k-anonymity suppression on small cohorts.

**AC:**
- [ ] Panel renders with city-matched cohort data
- [ ] Suppression label shown when cohort <5 sessions
- [ ] No cross-city leak (Montgomery session never sees Fort Worth cohort)
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.15 --- Suite: Sequence Viz + What-If Simulator | Cx: 10 | P1

**Description:**
`worker-sequence-viz.qc.yaml`. Open sequence viz → interact → toggle what-if scenarios → verify projections update.

**AC:**
- [ ] Viz renders with current plan sequence
- [ ] What-if toggle changes projection
- [ ] No console errors
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.16 --- Suite: Appointment Book → Confirmation | Cx: 10 | P1

**Description:**
`worker-apt-book.qc.yaml`. Book an appointment via UI → verify availability engine honored (no double-book) → confirmation shown → row in DB → email stub sent.

**AC:**
- [ ] Only valid slots bookable (double-book attempt rejected)
- [ ] Confirmation UI shown
- [ ] appointments row written
- [ ] Email send attempted (stubbed)
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.17 --- Suite: Appointment 24h Reminder → Manage-Link Cancel | Cx: 15 | P1

**Description:**
`worker-apt-reminder-cancel.qc.yaml`. Fake-clock advance to T-24h → reminder job fires → email stub captured → extract manage-link token → GET manage page → cancel → verify appointment row transitioned + audit written.

**AC:**
- [ ] Reminder email sent with valid manage-link
- [ ] GET /manage?action=cancel succeeds on valid token
- [ ] appointment status = cancelled
- [ ] Audit row written with action=appointment_cancel_via_link
- [ ] Second use of same token returns 401 (single-use enforced)
- [ ] Green on both cities

**Depends on:** T13.1, T13.2, T13.5

---

### T13.18 --- Suite: Appointment 1h Reminder → Reschedule | Cx: 10 | P1

**Description:**
`worker-apt-reminder-reschedule.qc.yaml`. Similar to T13.17 but T-1h reminder → reschedule action returns redirect hint.

**AC:**
- [ ] T-1h reminder sent
- [ ] Reschedule action returns redirect response shape
- [ ] No state mutation on redirect
- [ ] Green on both cities

**Depends on:** T13.1, T13.2, T13.5

---

### T13.19 --- Suite: Past-Appointment Auto-Advance | Cx: 10 | P1

**Description:**
`worker-apt-past-autoadvance.qc.yaml`. Fake-clock past appointment time → nightly orchestrator step 2.5 runs → scheduler.mark_missed fires → worker notice visible in digest → outcomes row filtered out of stall clock.

**AC:**
- [ ] Missed-appointment audit row written
- [ ] Worker notice renders in digest
- [ ] Stall clock unaffected (outcome marked `filtered`)
- [ ] Green on both cities

**Depends on:** T13.1, T13.2, T13.5

---

### T13.20 --- Suite: Resume Builder (LLM-Off Path) | Cx: 10 | P0

**Description:**
`worker-resume-llm-off.qc.yaml`. `ENABLE_AI_GENERATION=false` (default) → generate resume → template renders → PDF downloadable → version row written with `generation_method=template`.

**AC:**
- [ ] Resume generates via deterministic template
- [ ] PDF download returns valid PDF bytes (magic bytes check)
- [ ] resume_versions row has `generation_method=template`
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.21 --- Suite: Resume Builder (LLM-On + Injection Defense) | Cx: 15 | P0

**Description:**
`worker-resume-llm-on-injection.qc.yaml`. `ENABLE_AI_GENERATION=true` with mocked LLM → seed worker profile with injection payload (`ignore previous instructions...`) → generate → verify injection filter triggered, fallback template used, `generation_method=template_injection_blocked`, audit row written.

**AC:**
- [ ] Injection payload in worker field blocks LLM path
- [ ] Fallback template renders
- [ ] `generation_method=template_injection_blocked`
- [ ] Audit row with payload pattern logged
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.22 --- Suite: Cover Letter Fair-Chance Branch | Cx: 10 | P1

**Description:**
`worker-coverletter-fairchance.qc.yaml`. Demo session with `criminal.fair_chance_index` set → generate cover letter → verify fair-chance branch template used → verify no disclosure if flag off.

**AC:**
- [ ] Fair-chance index triggers fair-chance branch template
- [ ] Output mentions relevant fair-chance framing (template-specific string)
- [ ] Non-fair-chance session doesn't get that branch
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.23 --- Suite: Cover Letter Non-Fair-Chance Branch | Cx: 8 | P1

**Description:**
`worker-coverletter-default.qc.yaml`. Session without fair-chance index → default template path exercised end-to-end.

**AC:**
- [ ] Default template used
- [ ] No fair-chance content in output
- [ ] PDF valid
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.24 --- Suite: Jobs Kanban Add → Stages → Outcome | Cx: 15 | P1

**Description:**
`worker-jobs-kanban.qc.yaml`. Add job → drag through applied → interview → offer → marked outcome → outcomes row written → funnel stats update.

**AC:**
- [ ] Job card moves through stages via dnd-kit interactions
- [ ] Each stage persists
- [ ] Outcome marked → outcomes_records row written
- [ ] Funnel sidebar counts update
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.25 --- Suite: Jobs Kanban Resume-Version Attach | Cx: 10 | P1

**Description:**
`worker-jobs-attach-resume.qc.yaml`. Job card → attach existing resume version → verify use-counter increment → `generation_method` badge rendered.

**AC:**
- [ ] Resume attach UI allows selecting from version history
- [ ] use_count incremented on resume_versions row
- [ ] Badge reflects `generation_method`
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.26 --- Suite: Jobs Funnel Sidebar | Cx: 8 | P2

**Description:**
`worker-jobs-funnel.qc.yaml`. Verify funnel sidebar renders correctly for: empty state (no jobs), populated state (mixed stages), single-stage (all in applied).

**AC:**
- [ ] Empty state renders with "no jobs yet" copy
- [ ] Populated state shows correct counts per stage
- [ ] Conversion-rate math verified against demo data
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.27 --- Suite: Documents Versions Page | Cx: 10 | P1

**Description:**
`worker-docs-versions.qc.yaml`. Versions page → filter by type (resume/cover letter) → preview → re-download → delete older version → verify count.

**AC:**
- [ ] Versions render sorted by date desc
- [ ] Filter by type works
- [ ] Preview renders (PDF or HTML)
- [ ] Re-download returns same bytes
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.28 --- Suite: Engagement Preferences | Cx: 8 | P1

**Description:**
`worker-engagement-prefs.qc.yaml`. Toggle email reminder categories → save → verify reminder engine reads updated prefs → verify unsubscribed category does NOT receive next reminder.

**AC:**
- [ ] Preference toggles persist
- [ ] Reminder engine honors prefs on next run
- [ ] No reminder sent for disabled category
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.29 --- Suite: Reminder Delivery + Cooldown | Cx: 10 | P1

**Description:**
`worker-reminder-cooldown.qc.yaml`. Fire reminder → verify sent → fire again within cooldown → verify suppressed → advance clock past cooldown → verify sends.

**AC:**
- [ ] Initial reminder sent
- [ ] Second attempt within cooldown suppressed (audit row)
- [ ] Third attempt after cooldown sent
- [ ] Green on both cities

**Depends on:** T13.1, T13.2, T13.5

---

### T13.30 --- Suite: Unsubscribe GET (CAN-SPAM) | Cx: 10 | P0

**Description:**
`unauth-unsubscribe-get.qc.yaml`. Extract unsubscribe token from a sent reminder → GET /api/engagement/unsubscribe?token=... → verify 200 + opt-out row written → second GET of same token returns idempotent 200.

**AC:**
- [ ] GET succeeds on valid token
- [ ] reminders_auto_disabled row written
- [ ] Second GET returns uniform 200 (idempotent, CAN-SPAM requirement)
- [ ] Malformed token returns uniform 401 (no enumeration)
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.31 --- Suite: Unsubscribe POST (Idempotent) | Cx: 8 | P1

**Description:**
`unauth-unsubscribe-post.qc.yaml`. POST with valid token → 200 → second POST → still 200, no duplicate row.

**AC:**
- [ ] POST succeeds
- [ ] Single row in reminders_auto_disabled per session (not duplicated)
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.32 --- Suite: Weekly Review Page (Sunday Branch) | Cx: 15 | P1

**Description:**
`worker-weekly-review.qc.yaml`. Fake-clock to Sunday → nightly orchestrator runs Sunday branch → weekly review digest composed → page renders with funnel + engagement + barriers-cleared sections.

**AC:**
- [ ] Orchestrator takes Sunday branch
- [ ] Weekly review digest row written
- [ ] Page renders all three sections
- [ ] Non-Sunday runs don't trigger weekly review
- [ ] Green on both cities

**Depends on:** T13.1, T13.2, T13.5

---

### T13.33 --- Suite: Stall Alert Banner | Cx: 8 | P1

**Description:**
`worker-stall-banner.qc.yaml`. Stalled session → banner renders → dismiss → dismissed state persists in-session → re-appears on next stall threshold breach.

**AC:**
- [ ] Banner renders for stalled session
- [ ] Dismiss persists for session lifetime
- [ ] Hard-stall escalation re-shows banner
- [ ] Non-stalled session never sees banner
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.34 --- Suite: Voice Input | Cx: 10 | P2

**Description:**
`worker-voice-input.qc.yaml`. Start recording (mocked browser audio) → transcript returned → profile field populated.

**AC:**
- [ ] Record button triggers audio capture flow
- [ ] Mocked transcript populates target field
- [ ] Save persists
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.35 --- Suite: Share Outcome | Cx: 10 | P2

**Description:**
`worker-share-outcome.qc.yaml`. Generate share link → open in unauthenticated browser → verify public view renders → verify PII redacted.

**AC:**
- [ ] Share link generated
- [ ] Public view renders without auth
- [ ] No session ID, names, or PII visible
- [ ] Expired share link returns 404 or 410
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.36 --- Suite: Compliance Export Flow | Cx: 15 | P0

**Description:**
`worker-compliance-export.qc.yaml`. Request export → token issued → download archive → verify zip structure + SHA256-hashed filename → audit row written before archive build.

**AC:**
- [ ] POST /api/compliance/export returns download URL
- [ ] GET download returns zip with valid magic bytes
- [ ] Filename matches `worker-data-{16-hex}.zip` pattern
- [ ] compliance_audit row written with action=export_downloaded
- [ ] On build failure: export_failed row written, original exception preserved
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.37 --- Suite: Compliance Full Delete | Cx: 15 | P0

**Description:**
`worker-compliance-delete.qc.yaml`. Request full delete with confirm="DELETE" → cascade → verify zero rows in every session-scoped table → audit trail preserved.

**AC:**
- [ ] confirm != "DELETE" returns 400
- [ ] Valid delete cascades to every table referencing session_id
- [ ] Audit row written with actor_token hash
- [ ] Zero rows remain for session in appointments, jobs_applications, resume_versions, outcomes, etc.
- [ ] Audit row itself retained (immutable trail)
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.38 --- Suite: Compliance Selective Delete | Cx: 10 | P1

**Description:**
`worker-compliance-selective-delete.qc.yaml`. Per-module delete (e.g., delete documents only) → verify scope → other modules untouched → audit row.

**AC:**
- [ ] Selective delete by module scope
- [ ] Non-selected modules retain data
- [ ] Audit row enumerates scope
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.39 --- Suite: i18n EN↔ES Toggle Sweep | Cx: 15 | P1

**Description:**
`worker-i18n-toggle.qc.yaml`. Every top-level route loaded in EN → toggle to ES → re-load → assert no `t("key.missing")` outputs, no raw keys visible, layout stable (no clipped buttons).

**AC:**
- [ ] Every worker-facing route visited in both locales
- [ ] No untranslated key visible in rendered HTML
- [ ] Layout metric (overflow checks) stable
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

## Phase 3: Tier 1 Browser QC Suites --- Advisor Journeys

### T13.40 --- Suite: Advisor Login + Inbox + City Filter | Cx: 10 | P1

**Description:**
`advisor-login-inbox.qc.yaml`. Advisor auth token → inbox loads → sessions shown are city-scoped to advisor → cross-city session NOT visible.

**AC:**
- [ ] Advisor auth issues valid token
- [ ] Inbox renders with only advisor's city
- [ ] Cross-city probe via API returns 403
- [ ] Green for Montgomery advisor + Fort Worth advisor

**Depends on:** T13.1, T13.2

---

### T13.41 --- Suite: Stalled Sessions List + Select | Cx: 8 | P1

**Description:**
`advisor-stalled-select.qc.yaml`. Stalled sessions list → sort by stall duration → click session → detail view loads.

**AC:**
- [ ] List sorted by stall duration
- [ ] Click loads session detail
- [ ] Back button returns to list with sort preserved
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.42 --- Suite: Send Note → Audit → Worker View | Cx: 12 | P1

**Description:**
`advisor-send-note.qc.yaml`. Advisor sends note to worker → advisor audit row written → worker sees note in their inbox/digest → audit placeholder session row created once.

**AC:**
- [ ] Note send succeeds
- [ ] advisor_audit row written with kid-hashed actor
- [ ] Worker view shows note
- [ ] Advisor placeholder session created on first write, reused thereafter (INSERT OR IGNORE)
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.43 --- Suite: Module Status Dashboard | Cx: 8 | P2

**Description:**
`advisor-module-status.qc.yaml`. Status page renders → all modules report → partial failure surfaced → green/red reflect reality.

**AC:**
- [ ] All module statuses rendered
- [ ] Aggregator surfaces partial failures distinctly from total
- [ ] Timestamp of last collection visible
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.44 --- Suite: Stall Alert Banner Batch Dismiss | Cx: 8 | P2

**Description:**
`advisor-stall-banner.qc.yaml`. Banner on advisor view → batch dismiss → dismissed for advisor's session → other advisors still see banner.

**AC:**
- [ ] Batch dismiss persists per advisor
- [ ] Cross-advisor isolation verified
- [ ] Re-escalation after new stalls re-shows banner
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

## Phase 4: Tier 1 Browser QC Suites --- Admin Journeys

### T13.45 --- Suite: Feature Flag Toggle + Audit | Cx: 10 | P1

**Description:**
`admin-flag-toggle.qc.yaml`. Admin toggles a flag → audit row written → cache invalidated → UI reflects on next load.

**AC:**
- [ ] Flag toggle succeeds with valid admin key
- [ ] flag_audit row written
- [ ] Cache invalidated (next read returns new value)
- [ ] UI behavior reflects change
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.46 --- Suite: Engagement Kill-Switch Preflight | Cx: 8 | P1

**Description:**
`admin-kill-switch.qc.yaml`. Enable engagement kill-switch → next orchestrator run → verify reminder step skipped entirely.

**AC:**
- [ ] Kill-switch toggle persists
- [ ] Orchestrator checks preflight, skips step
- [ ] Skip audited
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.47 --- Suite: Rate-Limit Override Audit | Cx: 8 | P2

**Description:**
`admin-rate-limit-override.qc.yaml`. Exercise an admin override path → verify bypass_log.jsonl entry.

**AC:**
- [ ] Override succeeds with reason
- [ ] bypass_log entry written with actor + reason
- [ ] Without reason, override rejected
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.48 --- Suite: Admin-Key Gated Endpoints | Cx: 8 | P1

**Description:**
`admin-key-gate.qc.yaml`. No key → 422; wrong key → 403; correct key → 200; unconfigured key → 503.

**AC:**
- [ ] All four states exercised on every admin endpoint
- [ ] Responses match spec
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

## Phase 5: Tier 1 Browser QC Suites --- Unauthenticated Journeys

### T13.49 --- Suite: Expired Manage-Appointment Link | Cx: 5 | P1

**Description:**
`unauth-manage-expired.qc.yaml`. Expired token → uniform 401, no session disclosure.

**AC:**
- [ ] Expired token → 401 with uniform body
- [ ] No appointment_id leaked in response
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.50 --- Suite: Malformed Unsubscribe Token | Cx: 5 | P1

**Description:**
`unauth-unsubscribe-malformed.qc.yaml`. Malformed / tampered / replayed / unknown-kid token → uniform 401.

**AC:**
- [ ] All four failure modes return same 401 body
- [ ] No enumeration oracle (timing-consistent within tolerance)
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.51 --- Suite: Tampered Export Token | Cx: 5 | P1

**Description:**
`unauth-export-tampered.qc.yaml`. Export token with modified payload → 401 → no export generated.

**AC:**
- [ ] Tampered signature rejected
- [ ] No archive built
- [ ] No compliance_audit row for failed verify
- [ ] Green on both cities

**Depends on:** T13.1, T13.2

---

### T13.52 --- Suite: Key-Rotation Window | Cx: 10 | P1

**Description:**
`unauth-key-rotation.qc.yaml`. Sign token with old kid, verify during overlap window → 200. After overlap expires → 401.

**AC:**
- [ ] Old-kid token accepted during overlap
- [ ] Old-kid token rejected after overlap
- [ ] New-kid token accepted throughout
- [ ] Fake clock drives the window advance
- [ ] Green on both cities

**Depends on:** T13.1, T13.2, T13.5

---

## Phase 6: Tier 2 --- Backend Integration/E2E

### T13.53 --- Nightly Orchestrator Full Dry-Run | Cx: 20 | P0

**Description:**
pytest `test_orchestrator_full_run.py`. Stub demo data → run orchestrator → verify every step fires in order → verify outputs of each step.

**AC:**
- [ ] Every step in orchestrator pipeline invoked
- [ ] Ordering matches documented contract
- [ ] Partial-failure behavior verified (one step errors, others continue or halt per policy)
- [ ] Both cities exercised
- [ ] `bpsai-pair arch check` passes

**Depends on:** T13.2, T13.5

---

### T13.54 --- Scheduled Job Fire (APScheduler) | Cx: 15 | P1

**Description:**
`test_scheduler_fire.py`. Register job → advance fake clock → verify fire → verify side effects.

**AC:**
- [ ] Each registered job fires at expected time
- [ ] Missed-fire recovery behavior verified
- [ ] `bpsai-pair arch check` passes

**Depends on:** T13.5

---

### T13.55 --- SendGrid Webhook (Delivered/Bounced/Spam/Dropped) | Cx: 15 | P1

**Description:**
`test_sendgrid_webhook.py`. POST each event type → verify audit row written → verify engagement state updated (e.g., bounce → auto-disable).

**AC:**
- [ ] Each of 4 event types handled
- [ ] Audit rows written
- [ ] Bounce/spam events auto-disable reminders for that email
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T13.56 --- PDF Renderer SSRF Fuzz | Cx: 15 | P0

**Description:**
`test_pdf_ssrf_fuzz.py`. Every SSRF vector (metadata IPs 169.254, 127.0.0.1, file://, gopher://, redirect chain, DNS rebinding) → denied.

**AC:**
- [ ] Each vector returns URLFetchingError
- [ ] No network call made (verified via mock)
- [ ] Embedded `<img src=...>` in worker content blocked
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T13.57 --- Injection Filter Fuzz All Paths | Cx: 15 | P0

**Description:**
`test_injection_fuzz.py`. For every worker-controlled prompt input (resume, cover letter, job_description, job_match_ref.*, profile fields): exercise each with worst-case injection payloads.

**AC:**
- [ ] 50+ payload corpus (prompt injection primer)
- [ ] Every payload blocks LLM path
- [ ] Each input field verified independently
- [ ] Audit row captures matched pattern
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T13.58 --- Retention Sweep Scheduled | Cx: 10 | P1

**Description:**
`test_retention_sweep.py`. Aged sessions → sweep fires on schedule → cascaded delete → audit row.

**AC:**
- [ ] Aged-session detection correct
- [ ] Cascade reaches every session-scoped table
- [ ] Audit preserved
- [ ] `bpsai-pair arch check` passes

**Depends on:** T13.5

---

### T13.59 --- Audit-Log Integrity + Ordering | Cx: 15 | P0

**Description:**
`test_audit_integrity.py`. For every mutating API: exactly one audit row written; ordering preserved under failure (audit-before-build pattern); no double-writes on retry.

**AC:**
- [ ] Every mutating endpoint mapped to its audit shape
- [ ] Ordering verified under success + failure
- [ ] Idempotency keys prevent double-audit on retry
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T13.60 --- Rate Limiter Race + Boundary | Cx: 10 | P1

**Description:**
`test_rate_limiter_race.py`. Concurrent requests at boundary → exactly N allowed → window reset timing verified.

**AC:**
- [ ] Race produces deterministic allow/deny split
- [ ] No over-allow under concurrency
- [ ] Window reset honored
- [ ] `bpsai-pair arch check` passes

**Depends on:** T13.5

---

### T13.61 --- Unsubscribe Token Race | Cx: 10 | P1

**Description:**
`test_unsubscribe_race.py`. Two simultaneous GETs with same token → both 200, but single opt-out row.

**AC:**
- [ ] Concurrent GETs both succeed
- [ ] Exactly one opt-out row exists
- [ ] No double audit
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T13.62 --- Key Rotation Overlap | Cx: 10 | P1

**Description:**
`test_key_rotation_overlap.py`. Sign with old kid, verify during 7-day overlap → accept; after overlap → reject.

**AC:**
- [ ] Old-kid accepted within overlap
- [ ] Old-kid rejected after overlap
- [ ] Both kids accepted concurrently during overlap
- [ ] `bpsai-pair arch check` passes

**Depends on:** T13.5

---

### T13.63 --- Cross-Session Isolation All Endpoints | Cx: 20 | P0

**Description:**
`test_cross_session_isolation.py`. For every endpoint accepting a session token: attempt with cross-session token → 403 (not 401). Every endpoint mapped, no gaps.

**AC:**
- [ ] Endpoint inventory generated from FastAPI router introspection
- [ ] Every endpoint tested with valid-but-wrong-session token
- [ ] 403 response confirmed
- [ ] Any endpoint returning 200 on cross-session → test fails
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T13.64 --- Feature Flag State Machine Race | Cx: 10 | P2

**Description:**
`test_flag_race.py`. Concurrent toggle + read → cache coherence → audit gap detection.

**AC:**
- [ ] Concurrent toggle + 100 reads → final cache state correct
- [ ] Audit row count matches toggle count
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T13.65 --- Plan Refresher Trigger Matrix | Cx: 15 | P1

**Description:**
`test_plan_refresher_matrix.py`. Every (trigger type × window boundary × carry-forward edge) combination exercised.

**AC:**
- [ ] Matrix enumeration covers: stall_hard, barrier_resolved, both, neither
- [ ] Carry-forward: empty prior plan, partial match, full match, no-match
- [ ] 20-row cap enforced
- [ ] `bpsai-pair arch check` passes

**Depends on:** T13.5

---

### T13.66 --- Weekly Review Window Boundaries | Cx: 10 | P1

**Description:**
`test_weekly_review_boundaries.py`. Session created mid-week, no engagement data, fully-engaged data, DST transition within window.

**AC:**
- [ ] Mid-week session: partial window handled
- [ ] No-data session: graceful empty digest
- [ ] DST boundary: correct 7 days counted
- [ ] `bpsai-pair arch check` passes

**Depends on:** T13.5

---

### T13.67 --- Demo Seed Every-Feature Check | Cx: 10 | P1

**Description:**
`test_demo_seed_coverage.py`. Assert every module has at least one demo session exercising it (coverage assertion).

**AC:**
- [ ] Module inventory generated from module_status_contracts
- [ ] Every module covered by ≥1 demo session
- [ ] Test fails if a new module is added without seed update
- [ ] `bpsai-pair arch check` passes

**Depends on:** T13.2

---

### T13.68 --- i18n Backend String Completeness | Cx: 8 | P1

**Description:**
`test_i18n_completeness.py`. For every server-rendered string key: verify EN + ES entries exist; verify no key missing in either.

**AC:**
- [ ] en.json and es.json same key set
- [ ] No key with empty value
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T13.69 --- Module Status Aggregator | Cx: 10 | P1

**Description:**
`test_module_status_aggregator.py`. Partial failure, total failure, all-green — aggregator shape and error surfacing correct.

**AC:**
- [ ] All-green shape verified
- [ ] Partial-failure surfaced distinctly
- [ ] Total-failure returns aggregator-level error
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T13.70 --- Compliance Cascade Verification | Cx: 15 | P0

**Description:**
`test_compliance_cascade.py`. Enumerate every table with a session_id FK → full_delete → assert zero rows in each. Test fails if a new session-scoped table is added without cascade.

**AC:**
- [ ] Table inventory generated via schema introspection
- [ ] full_delete followed by count(*)==0 on every listed table
- [ ] Audit row retained (explicit exception)
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

## Phase 7: Tier 3 --- Exploratory Agent Sweeps

### T13.71 --- Sweep: Cross-Session Data Leak Attempt | Cx: 20 | P0

**Description:**
Launch `general-purpose` agent tasked with "try to leak another worker's data using only public endpoints". Report findings. Each finding becomes a sub-fix task.

**AC:**
- [ ] Agent exercised for ≥30 min of tool budget
- [ ] Report filed as `docs/qc-reports/S13-T71-cross-session.md`
- [ ] Zero findings OR findings tracked as sub-tasks

**Depends on:** Phases 1–5 complete

---

### T13.72 --- Sweep: Empty-Profile Page Breakage | Cx: 15 | P1

**Description:**
Agent task: "Find every page that breaks or shows ugly empty states with an unpopulated worker profile." Report.

**AC:**
- [ ] Every top-level route visited with empty profile
- [ ] Report filed; findings tracked
- [ ] Each finding → sub-task fix

**Depends on:** Phases 1–5 complete

---

### T13.73 --- Sweep: Slow-Network Breakage | Cx: 15 | P1

**Description:**
Agent task with Chrome devtools throttled to 3G: exercise every golden path, report timeouts, spinner-forever states, race conditions.

**AC:**
- [ ] Every golden path exercised under throttle
- [ ] Timeout/forever-spinner states catalogued
- [ ] Report filed

**Depends on:** Phases 1–5 complete

---

### T13.74 --- Sweep: Pathological Input Fuzz | Cx: 20 | P1

**Description:**
Agent submits every form with emoji, RTL, zero-width, 10KB strings, null bytes, SQL fragments, HTML tags, unicode normalization attacks.

**AC:**
- [ ] Every form exercised with corpus
- [ ] Rendering failures catalogued
- [ ] Server errors catalogued
- [ ] Report filed

**Depends on:** Phases 1–5 complete

---

### T13.75 --- Sweep: Random-Click Stability | Cx: 15 | P2

**Description:**
Agent clicks every interactive element in random order for 30 min. Reports anything weird (broken state, 500s, infinite loops).

**AC:**
- [ ] ≥30 min exercise
- [ ] Console errors captured
- [ ] Network failures captured
- [ ] Report filed

**Depends on:** Phases 1–5 complete

---

### T13.76 --- Sweep: Multi-Tab Stale-State | Cx: 15 | P1

**Description:**
Agent opens same session in two tabs, performs conflicting operations, reports stale-state bugs.

**AC:**
- [ ] Cross-tab write conflicts catalogued
- [ ] Stale-cache bugs catalogued
- [ ] Report filed

**Depends on:** Phases 1–5 complete

---

### T13.77 --- Sweep: ES-Locale Full Platform | Cx: 15 | P1

**Description:**
Agent exercises every feature in ES locale. Reports untranslated strings, layout clips, copy issues.

**AC:**
- [ ] Every feature visited in ES
- [ ] Layout/truncation issues captured
- [ ] Untranslated strings catalogued
- [ ] Report filed

**Depends on:** T13.39, Phases 1–5 complete

---

## Phase 8: Tier 4 --- Cross-Cutting Quality Gates

### T13.78 --- i18n Completeness Audit | Cx: 10 | P1

**Description:**
Static analysis over the frontend: every JSX string literal wrapped in `t()`, every `t()` key exists in both locales, no orphaned keys.

**AC:**
- [ ] Lint rule or custom script enforces `t()` wrapping
- [ ] CI job verifies on every PR
- [ ] Current orphans/missing keys fixed
- [ ] `bpsai-pair arch check` passes

**Depends on:** T13.68

---

### T13.79 --- a11y axe-core Sweep Every Route (WCAG AAA) | Cx: 15 | P1

**Description:**
Automated axe-core sweep of every route in both locales, configured to WCAG 2.1 AAA ruleset. Violations catalogued and fixed.

**AC:**
- [ ] axe configured with `tags: ['wcag2aaa', 'wcag21aaa']`
- [ ] Every top-level route sweeped in en + es
- [ ] Zero serious/critical violations at AAA
- [ ] Moderate violations fixed or documented with WCAG-AAA-specific exception rationale
- [ ] `bpsai-pair arch check` passes

**Depends on:** T13.4

---

### T13.80 --- a11y Keyboard-Only Nav Critical Paths (AAA) | Cx: 15 | P1

**Description:**
Manual keyboard-only traversal of the five submission-critical paths, applying AAA criteria (e.g., 2.4.8 location, 2.4.9 link purpose link-only, 2.4.10 section headings).

**AC:**
- [ ] Five submission-critical paths traversed keyboard-only
- [ ] Tab order logical (source-order or explicit tabindex)
- [ ] Focus visible on every interactive element
- [ ] Focus trap on modals works (tab cycles inside; esc closes)
- [ ] Current location indicator present on every page (WCAG 2.4.8)
- [ ] Links self-describe out of context (WCAG 2.4.9)

**Depends on:** none

---

### T13.81 --- a11y Screen-Reader Pass (AAA) | Cx: 15 | P1

**Description:**
VoiceOver (macOS) + NVDA (Windows) pass on the five critical flows. AAA criteria including 1.4.6 (enhanced contrast), 2.4.10 (section headings), 3.1.5 (reading level).

**AC:**
- [ ] Five critical flows exercised with VoiceOver AND NVDA
- [ ] Every interactive element has accessible name
- [ ] Landmarks present (main, nav, complementary)
- [ ] Live regions announce updates (digest refresh, form submit)
- [ ] Section headings present (WCAG 2.4.10)
- [ ] Reading level documented; lower-secondary-education-level alternatives provided where flagged (WCAG 3.1.5)

**Depends on:** none

---

### T13.82 --- Color Contrast WCAG AAA | Cx: 10 | P1

**Description:**
Automated contrast audit of every foreground/background pair in the design system at AAA thresholds. Failures fixed at token level, not per-instance.

**AC:**
- [ ] Contrast checker run over design tokens at AAA thresholds
- [ ] Every pair meets 7:1 (normal text) or 4.5:1 (large text) — WCAG 1.4.6
- [ ] Failures fixed in token definitions

**Depends on:** none

---

### T13.83 --- Visual Regression Baseline | Cx: 20 | P1

**Description:**
Establish baseline screenshots for every top-level route × city × locale. Diff against baseline on every PR.

**AC:**
- [ ] Baseline captured
- [ ] CI job runs diff on every PR
- [ ] Baseline update process documented
- [ ] `bpsai-pair arch check` passes

**Depends on:** T13.6

---

### T13.84 --- Responsive Viewport Matrix | Cx: 15 | P1

**Description:**
Every page verified at 360 / 768 / 1024 / 1440 px. Document any breakpoint issues.

**AC:**
- [ ] All 4 widths exercised on every top-level route
- [ ] Layout issues catalogued as sub-fixes
- [ ] No horizontal scroll on <768px

**Depends on:** none

---

### T13.85 --- Cross-Browser Matrix | Cx: 20 | P1

**Description:**
Latest Chrome, Safari, Firefox on desktop; Mobile Safari (iOS), Chrome Android on mobile. Every golden path verified.

**AC:**
- [ ] 5 browsers × 6 golden paths exercised
- [ ] Browser-specific bugs catalogued
- [ ] Feature-detection / polyfills added if needed

**Depends on:** Phases 1–5 complete

---

### T13.86 --- Lighthouse Every Route | Cx: 10 | P1

**Description:**
Lighthouse full run on every top-level route. Hit targets: Perf ≥90, A11y ≥95, Best Practices ≥95, SEO ≥95 (T7 targets; may be relaxed to T4 floors per T13.7 policy).

**AC:**
- [ ] Every top-level route scored
- [ ] Score floors hit or documented exception
- [ ] Largest-hit optimizations applied

**Depends on:** T13.7

---

### T13.87 --- Bundle Size Audit | Cx: 10 | P2

**Description:**
Bundle analyzer on production build. Identify largest deps, flag unexpected sizes, document budget.

**AC:**
- [ ] Analyzer report generated
- [ ] Per-route budget documented
- [ ] CI job fails on regression >10%

**Depends on:** none

---

### T13.88 --- TTFB / API Perf Profile | Cx: 15 | P2

**Description:**
Load test every API endpoint with realistic payload size. Measure p50/p95/p99 TTFB. Document budgets.

**AC:**
- [ ] Every endpoint profiled
- [ ] p95 <500ms for read endpoints; <2s for write
- [ ] Slow endpoints flagged for optimization
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T13.89 --- Nightly Orchestrator Runtime Budget | Cx: 10 | P2

**Description:**
Measure full orchestrator run time under realistic demo data. Budget documented. Slow steps profiled.

**AC:**
- [ ] Run time measured across 10 runs
- [ ] p95 budget documented (e.g., <60s for 100 sessions)
- [ ] Bottleneck steps identified
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T13.90 --- N+1 Query Audit | Cx: 15 | P1

**Description:**
SQL log analysis on every top endpoint. Identify N+1 patterns. Fix via batched queries or eager loading.

**AC:**
- [ ] Query logger enabled for test run
- [ ] Every endpoint's query count documented
- [ ] N+1 patterns flagged; fixes applied
- [ ] `bpsai-pair arch check` passes

**Depends on:** none

---

### T13.91 --- Offline / Slow-3G Resilience | Cx: 10 | P2

**Description:**
Chrome devtools offline mode: graceful error states. 3G throttle: acceptable loading UX.

**AC:**
- [ ] Offline: clear error UI, no infinite spinner
- [ ] 3G: loading states visible within 1s
- [ ] Requests have sensible timeouts

**Depends on:** T13.73

---

### T13.92 --- Request Timeout / Retry Behavior | Cx: 10 | P2

**Description:**
Every fetch has an explicit timeout. Retries with exponential backoff where idempotent. Non-idempotent requests don't retry silently.

**AC:**
- [ ] Every fetch has explicit timeout
- [ ] Idempotent endpoints retry with backoff
- [ ] Non-idempotent endpoints surface errors instead of retrying

**Depends on:** none

---

## Phase 9: Tier 5 --- Security + Compliance Audit (laverna-driven)

### T13.93 --- Token Scope Audit | Cx: 15 | P0

**Description:**
`laverna` pass: every token type (feedback, session, unsubscribe, export, manage-appointment, admin, advisor, download) scoped correctly. No over-privileged token.

**AC:**
- [ ] Report filed: one row per token type × claims × enforcement site
- [ ] Any over-privileged token → fix sub-task
- [ ] Report reviewed by user before sign-off

**Depends on:** none

---

### T13.94 --- PII Log Scrub Audit | Cx: 10 | P0

**Description:**
Log corpus review. No raw session IDs, names, emails, or worker content in structured logs.

**AC:**
- [ ] Sample log corpus from a full orchestrator run reviewed
- [ ] Any PII found → redaction sub-task
- [ ] Log scrubber centralized

**Depends on:** none

---

### T13.95 --- SSRF Surface Full Sweep | Cx: 15 | P0

**Description:**
Every URL-fetching code path (weasyprint url_fetcher, markdown image refs, any outbound HTTP) reviewed for SSRF protection.

**AC:**
- [ ] Inventory of URL-fetching sites
- [ ] Every site has a deny-all or allowlist
- [ ] T13.56 fuzz tests cover each
- [ ] Report filed

**Depends on:** T13.56

---

### T13.96 --- XSS Audit (Every Render) | Cx: 15 | P0

**Description:**
Every user-content-render site: Jinja2 autoescape on, React defaults honored, markdown output HTML-escaped.

**AC:**
- [ ] Every render site catalogued
- [ ] Autoescape verified
- [ ] dangerouslySetInnerHTML uses reviewed and justified
- [ ] Markdown sanitization confirmed

**Depends on:** none

---

### T13.97 --- SQLi Audit | Cx: 10 | P0

**Description:**
Every query reviewed. No string concatenation. Parameterized everywhere. Any dynamic identifier (table/column) allowlisted.

**AC:**
- [ ] Query inventory generated
- [ ] Every query parameterized
- [ ] Any dynamic identifier traced back to allowlist
- [ ] Report filed

**Depends on:** none

---

### T13.98 --- CSRF Audit | Cx: 10 | P1

**Description:**
Every state-changing POST has CSRF protection (token, SameSite=Strict, or equivalent).

**AC:**
- [ ] Every mutating endpoint documented with its CSRF story
- [ ] Gaps fixed
- [ ] Report filed

**Depends on:** none

---

### T13.99 --- Rate-Limit Coverage Audit | Cx: 10 | P1

**Description:**
Every mutating endpoint has a rate limit. Limits sane (not too tight, not too loose). Admin endpoints have separate limits.

**AC:**
- [ ] Endpoint × limit table generated
- [ ] Missing limits added
- [ ] Limit values reviewed

**Depends on:** none

---

### T13.100 --- CAN-SPAM Compliance Audit | Cx: 10 | P0

**Description:**
Every engagement email reviewed: GET+POST unsubscribe, identification, physical postal address in footer, 10-day honor window.

**AC:**
- [ ] Template inventory
- [ ] Each template has compliant footer
- [ ] Unsubscribe honored within 10 days (audit trail verifies)
- [ ] Postal address configured

**Depends on:** none

---

### T13.101 --- GDPR-Adjacent Export/Delete Verify | Cx: 10 | P0

**Description:**
Export returns complete data; delete cascades; right-to-access documented publicly.

**AC:**
- [ ] Export archive contains every session-scoped table's data
- [ ] Delete cascade verified (overlaps with T13.70)
- [ ] Public doc for data rights
- [ ] Report filed

**Depends on:** T13.70

---

### T13.102 --- Audit Trail Completeness | Cx: 10 | P1

**Description:**
Every mutating action produces exactly one audit row. Trail queryable per session and per actor.

**AC:**
- [ ] Every mutating endpoint audited (overlaps with T13.59)
- [ ] Query-per-session + query-per-actor verified
- [ ] Immutability constraint documented

**Depends on:** T13.59

---

### T13.103 --- Secret Hygiene Sweep | Cx: 10 | P0

**Description:**
No secrets in repo (git history scan). `.env*` in .gitignore. CI logs don't leak.

**AC:**
- [ ] git-secrets or gitleaks run on full history
- [ ] .gitignore verified
- [ ] CI log inspection for any secret pattern
- [ ] Remediation plan for any historical leak (rotation)

**Depends on:** none

---

### T13.104 --- CVE Surveillance Setup | Cx: 10 | P1

**Description:**
pip-audit + npm audit wired in CI (already there for pip). Dependabot or Renovate configured. Weekly alert to a channel.

**AC:**
- [ ] Dependabot/Renovate config checked in
- [ ] Weekly report destination configured
- [ ] Existing CVEs resolved or documented

**Depends on:** none

---

## Phase 10: Tier 6 --- Cross-Module Integrity (vaivora-driven)

### T13.105 --- Schema/FK/Enum Contract Check | Cx: 15 | P1

**Description:**
`vaivora` pass: every FK honored, every enum synced between backend (Python) and frontend (TS).

**AC:**
- [ ] FK inventory; zero broken FKs
- [ ] Enum inventory; backend ↔ frontend match
- [ ] Mismatches → sub-fix tasks

**Depends on:** none

---

### T13.106 --- Event Ordering Stability | Cx: 10 | P1

**Description:**
Event-driven coupling (appointment.attended, barrier.cleared, etc.) — ordering stable under load.

**AC:**
- [ ] Event emission points catalogued
- [ ] Ordering contract documented
- [ ] Test under concurrent emission verifies ordering

**Depends on:** none

---

### T13.107 --- Status Contract Shape Check | Cx: 10 | P1

**Description:**
Every module's `nightly_status` shape matches aggregator expectation. No drift.

**AC:**
- [ ] Module × shape table
- [ ] Aggregator schema documented
- [ ] Drift detection in aggregator (reject unknown keys)

**Depends on:** T13.69

---

### T13.108 --- Shared Taxonomy Source-of-Truth Audit | Cx: 10 | P1

**Description:**
phase, category, stage, barrier_type — one source of truth per taxonomy. No drift between modules.

**AC:**
- [ ] Taxonomy inventory
- [ ] Single source per taxonomy identified
- [ ] Drift cases → sub-fix

**Depends on:** none

---

### T13.109 --- Migration Re-Run Safety | Cx: 10 | P1

**Description:**
Every migration re-runnable (idempotent) or documented as down-safe.

**AC:**
- [ ] Every migration re-run produces no errors
- [ ] Down migrations exist or absence documented

**Depends on:** none

---

### T13.110 --- Module Boundary Violation Scan | Cx: 10 | P2

**Description:**
Static analysis: no module reaches into another's private `_*` helpers. Boundary violations → sub-fix.

**AC:**
- [ ] Import graph generated
- [ ] Private-symbol imports across module boundaries flagged
- [ ] Violations fixed

**Depends on:** none

---

## Phase 11: Tier 7 --- Submission Readiness

### T13.111 --- Demo Script Dry-Run | Cx: 10 | P0

**Description:**
The full submission demo script executed end-to-end. Every beat works. Timing verified.

**AC:**
- [ ] Demo script document exists in `docs/submission-demo.md`
- [ ] Every beat exercised successfully
- [ ] Timing logged

**Depends on:** all prior phases complete

---

### T13.112 --- Stakeholder Walkthrough | Cx: 10 | P1

**Description:**
Someone who hasn't seen the product walks through the demo. Feedback captured.

**AC:**
- [ ] Walkthrough completed
- [ ] Feedback document filed
- [ ] Findings → sub-fix tasks

**Depends on:** T13.111

---

### T13.113 --- Lighthouse Target Hit | Cx: 5 | P1

**Description:**
Perf ≥90, A11y ≥95, Best Practices ≥95, SEO ≥95 on every top-level route.

**AC:**
- [ ] Lighthouse run recorded for every route
- [ ] Targets met or exception documented

**Depends on:** T13.86

---

### T13.114 --- 404 + 500 Branded Pages | Cx: 8 | P1

**Description:**
Custom 404 and 500 pages with brand styling and useful copy.

**AC:**
- [ ] 404 page renders on unknown route
- [ ] 500 page renders on server error (stubbed)
- [ ] Both pages responsive + i18n

**Depends on:** none

---

### T13.115 --- Privacy Policy + Terms + Legal Footer (Authored Fresh) | Cx: 20 | P1

**Description:**
Author privacy policy and terms of service from scratch (no template attribution). GDPR + CCPA + COPPA-aware. Cover: data collected (PII, session content, advisor notes), purposes (matching, compliance, audit), retention (90d post-expiry sweep), worker rights (access, export, delete), advisor data handling, third-party processors (SendGrid, LLM providers). Legal footer on every page linking both + company legal entity.

**AC:**
- [ ] /privacy renders authored policy covering all data flows
- [ ] /terms renders authored ToS
- [ ] Footer on every page links to both + entity name
- [ ] Counsel review checkbox in PR description before merge
- [ ] Both pages i18n (en + es)

**Depends on:** none

---

### T13.116 --- Favicon + PWA Manifest + OG/Twitter Meta | Cx: 8 | P1

**Description:**
Full meta suite: favicon in multiple sizes, PWA manifest, OpenGraph + Twitter card meta on every top-level route.

**AC:**
- [ ] Favicon 16/32/180 (apple-touch)/192/512
- [ ] manifest.json with icons + colors
- [ ] OG + Twitter meta on home + daily + shared outcome pages
- [ ] og:image present

**Depends on:** none

---

### T13.117 --- Sitemap + robots.txt | Cx: 5 | P2

**Description:**
Sitemap.xml generated from routes. robots.txt with sensible defaults (block /admin, /api).

**AC:**
- [ ] /sitemap.xml valid
- [ ] /robots.txt served
- [ ] Admin routes disallowed

**Depends on:** none

---

### T13.118 --- Production Env Audit | Cx: 10 | P0

**Description:**
Every env var used by code documented in `.env.example`. Production values configured in deploy target. Missing required vars fail fast on boot.

**AC:**
- [ ] .env.example complete
- [ ] Startup check verifies required vars present
- [ ] Deploy target (staging/prod) has each var

**Depends on:** none

---

### T13.119 --- [CANCELLED hackathon] Staging → Prod Migration Dry-Run | Cx: 15 | P2

**Description:**
Full migration chain run against a prod-like snapshot in staging. Any issues caught here, not in prod.

**AC:**
- [ ] Snapshot of prod-like data created
- [ ] Migrations applied end-to-end
- [ ] Rollback tested
- [ ] Dry-run report filed

**Depends on:** none

---

### T13.120 --- Rollback Plan Documented | Cx: 10 | P0

**Description:**
`docs/runbooks/rollback.md` covers: app rollback, DB rollback, feature-flag rollback, emergency kill-switch.

**AC:**
- [ ] Runbook exists with step-by-step for each scenario
- [ ] Each scenario rehearsed once
- [ ] Contact/escalation paths documented

**Depends on:** none

---

### T13.121 --- [CANCELLED hackathon] Post-Launch Monitoring Wired (Sentry) | Cx: 20 | P2

**Description:**
Sentry (recommended; alternatives acceptable) wired backend + frontend. Source map upload from frontend build. PII scrubbed before send. Uptime monitoring on critical endpoints. Alerts route to a human-reachable channel.

**AC:**
- [ ] Error tracking captures backend + frontend errors
- [ ] Uptime check on critical endpoints
- [ ] Alerts route to a human-reachable channel
- [ ] Sample error triggers alert end-to-end

**Depends on:** none

---

### T13.122 --- [CANCELLED hackathon] Backup + Restore Rehearsal | Cx: 10 | P2

**Description:**
Backup of prod data to a safe location. Restore rehearsed end-to-end into a fresh environment.

**AC:**
- [ ] Automated backup schedule documented + working
- [ ] Restore rehearsed with integrity check
- [ ] RPO/RTO documented

**Depends on:** none

---

### T13.123 --- [CANCELLED hackathon] On-Call Rotation | Cx: 8 | P2

**Description:**
Submission targets prod rollout, so on-call is required. Rotation, escalation matrix, paging tool, and runbook ownership documented.

**AC:**
- [ ] Rotation defined with at least two people
- [ ] Paging tool wired to alerts from T13.121
- [ ] Escalation matrix documented (severity → response time → escalation path)
- [ ] Runbooks indexed and reachable by rotation

**Depends on:** none

---

## Phase 12: Continuous QC

### T13.124 --- [CANCELLED hackathon] Nightly QC Against Staging | Cx: 15 | P2

**Description:**
Scheduled GitHub Action: nightly run of critical QC suites against staging. Results posted to dashboard + alerting channel on regression.

**AC:**
- [ ] Scheduled workflow exists
- [ ] Runs top 10 critical suites
- [ ] Regression alerts route correctly
- [ ] Failure report readable

**Depends on:** T13.8, staging env

---

### T13.125 --- Critical QC Suites in CI (Every PR) | Cx: 15 | P2

**Description:**
Add a CI job that runs the top 5 QC suites headlessly via Playwright on every PR. Depends on T13.129 Playwright harness.

**AC:**
- [ ] CI job defined
- [ ] 5 critical suites run headlessly
- [ ] Failures block merge
- [ ] Run time <10 min

**Depends on:** T13.1

---

### T13.126 --- [CANCELLED hackathon] Flake Detection + Retry Classifier | Cx: 15 | P2

**Description:**
Track suite pass/fail across runs. Flakes (pass+fail in last 5 runs) surfaced. Auto-retry once for transient failures, classify as flake vs real.

**AC:**
- [ ] Flake detection in QC dashboard
- [ ] Auto-retry policy documented
- [ ] Flake list reviewed weekly (manual for now)

**Depends on:** T13.8

---

### T13.127 --- [CANCELLED hackathon] Bug Tracker Integration | Cx: 10 | P2

**Description:**
Failing QC suites open tickets automatically (Trello or configured PM provider).

**AC:**
- [ ] QC run failure → ticket created
- [ ] Dedup: same suite failing again updates the open ticket
- [ ] Resolved ticket closes on suite going green

**Depends on:** T13.8

---

## Phase 13: Decision-Locked Additions

### T13.128 --- Stand Up Staging Environment | Cx: 25 | P0

**Description:**
Provision a staging environment (recommend: same stack as prod target — Docker Compose host, managed Postgres if migrating off SQLite, or sticking with SQLite + persistent volume if intentional). Deploy current main. Smoke-test every top-level route. Hook to a staging.* DNS subdomain. Document deploy + rollback in runbook.

**AC:**
- [ ] Staging deployed at a stable URL
- [ ] DB seeded with demo data via T13.2 + T13.3
- [ ] Every top-level route returns 200 in smoke check
- [ ] Deploy + rollback runbook in `docs/runbooks/staging-deploy.md`
- [ ] `.paircoder/qc/config.yaml` `staging` profile points at the staging URL

**Depends on:** none

---

### T13.129 --- Playwright Headless Harness | Cx: 15 | P1

**Description:**
Install Playwright in `frontend/` devDependencies. Configure to run a subset of `.qc.yaml` suites (or write Playwright equivalents) headlessly so CI can execute them on every PR. Document the divona-vs-Playwright split: divona for full interactive QC author-time and broad coverage; Playwright for the top-5 critical-path subset gated on every PR.

**AC:**
- [ ] `playwright` + `@playwright/test` in frontend/package.json devDependencies
- [ ] Headless config runs against local dev server
- [ ] At least one suite (`worker-onboarding`) runs in both divona and Playwright; results match
- [ ] Documentation in `.paircoder/qc/suites/README.md` covers when to use which runner
- [ ] `bpsai-pair arch check` passes

**Depends on:** T13.1

---

## Summary by Phase

| Phase | Tasks | Cx | Focus |
|---|---|---|---|
| 1 Infrastructure | 8 | 130 | QC config, demo seed ext, reset CLI, axe-core, fake clock, screenshot, Lighthouse, dashboard |
| 2 Tier-1 Worker suites | 30 | 315 | Every worker journey end-to-end |
| 3 Tier-1 Advisor suites | 5 | 46 | Advisor inbox flows |
| 4 Tier-1 Admin suites | 4 | 34 | Flag, kill-switch, rate-limit, admin-key |
| 5 Tier-1 Unauth suites | 4 | 25 | Token rejection surfaces |
| 6 Tier-2 Backend e2e | 18 | 233 | Orchestrator, jobs, webhooks, SSRF, injection, isolation |
| 7 Tier-3 Exploratory | 7 | 115 | Agent-driven adversarial sweeps |
| 8 Tier-4 Cross-cutting | 15 | 205 | i18n, a11y, visual, perf, responsive, cross-browser |
| 9 Tier-5 Security | 12 | 135 | Tokens, PII, SSRF, XSS, SQLi, CSRF, rate, CAN-SPAM, GDPR, audit, secrets, CVEs |
| 10 Tier-6 Cross-module | 6 | 65 | Schema, events, status, taxonomy, migrations, boundaries |
| 11 Tier-7 Submission | 13 | 131 | Demo, legal, favicon, env, migration, rollback, monitoring, backup |
| 12 Continuous | 4 | 55 | Nightly, PR-gated, flake detect, bug tracker |
| 13 Decision-locked additions | 2 | 40 | Staging stand-up, Playwright harness |
| **Total** | **128** | **1,545** | |

*(Cx totals per phase differ slightly from sum-of-task-Cx above due to rounding; official task-by-task Cx is authoritative.)*

## Summary by Priority

- **P0 (12 tasks, ~160 Cx)**: QC foundation (T13.1, T13.2, T13.3), critical suites (T13.10, T13.11, T13.20, T13.21, T13.30, T13.36, T13.37), backend blockers (T13.53, T13.56, T13.57, T13.59, T13.63, T13.70), exploratory leak sweep (T13.71), security (T13.93, T13.94, T13.95, T13.96, T13.97, T13.100, T13.101, T13.103), submission (T13.111, T13.115, T13.118, T13.120)
- **P1 (~74 tasks)**: Core suite coverage, cross-cutting audits, most backend e2e, most security/cross-module audits, most submission polish
- **P2 (~40 tasks)**: Polish suites, nice-to-have coverage, tooling deferrables

## Cross-Sprint Dependencies

- Must follow S12b (merged as PR #63, commit 7b4d85e)
- **Net-new env vars**: `LIGHTHOUSE_CI_TOKEN` (T13.7), `SENTRY_DSN` if decision #3 = Sentry (T13.121)
- **Net-new deps**: `@axe-core/react` (T13.4), Playwright or `pixelmatch` (T13.6, gated), `@lhci/cli` (T13.7), `gitleaks` (T13.103)
- **Net-new migrations**: none expected (demo seed ext works with existing schema)
- **No new features for workers or advisors** — verification only

## Risks + Mitigations

| Risk | Mitigation |
|---|---|
| QC suite infrastructure doesn't work reliably with divona → blocks Phase 2–5 | T13.1 authors + validates template end-to-end before Phase 2 begins; ship a reference suite in T13.10 as smoke test |
| Demo seed doesn't cover a feature → suites can't exercise it | T13.2 coverage assertion + T13.67 auto-check on every module addition |
| Browser QC is manual → slow feedback loop | T13.125 adds headless CI runs if decision #5 allows; T13.124 adds nightly staging run |
| Staging env doesn't exist → T13.119, T13.124 blocked | User decision #1 resolves; if staging deferred, those tasks defer too |
| Security findings require rework during submission window | laverna pass (Phase 9) runs as early as possible; P0 findings block submission explicitly |
| Fake-clock harness breaks existing tests | T13.5 migrates one test as proof; expand slowly, keep wall-clock tests as fallback |
| Visual regression introduces flakes | T13.6 threshold + T13.126 flake detection; treat visual diff as advisory initially |
| Cross-browser bugs require major rework | T13.85 runs early to surface; Chrome-only fallback is acceptable for submission per user direction |
| Legal pages require counsel | Decision #7 resolves; template + counsel review both valid paths |
| Error tracking addition touches every handler | T13.121 uses middleware pattern; no per-handler edits |

## Post-S13 Opportunities (explicitly deferred)

- S12b engineering carryover: APP_HOST helper, shared documents-builder helpers, token-system unification, advisor-audit schema consolidation, rate-limiter consolidation, unsubscribe endpoint double-connection
- Accessibility AAA upgrade (if AA only in this sprint)
- Load testing beyond TTFB (concurrent 100s of sessions, sustained load)
- Chaos testing (random dep failures)
- Canary release framework
- Feature flag progressive rollout automation
- A/B testing framework
- Analytics instrumentation
- Customer support tooling

## Explicitly Not in Scope

- Any net-new product feature
- Schema/architectural refactors (carried to S14+)
- Non-submission improvements
- Performance optimization beyond meeting Lighthouse floors
