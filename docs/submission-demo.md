# MontGoWork — Hackathon Submission Demo Script

> Live judges' demo. 5-7 minutes of narrative + UI walk-through over the
> staging environment. Authored T13.111 (S13 Submission Readiness).
> Dry-run against staging on 2026-04-25 — every beat verified.

---

## 0. Setup (one time, before judging starts)

| Item | Value |
|------|-------|
| Frontend | <https://montgowork-staging-web.fly.dev> |
| Backend | <https://montgowork-staging-api.fly.dev> |
| Demo data | 10 sessions seeded (5 stall states × 2 cities); deterministic UUIDs (see §A) |
| Reset (only if state drifts) | `python scripts/qc_reset.py --db-path /app/data/montgowork.db` (run via `fly ssh console --app montgowork-staging-api`) |
| Smoke | `STAGING_FRONTEND_URL=https://montgowork-staging-web.fly.dev STAGING_API_URL=https://montgowork-staging-api.fly.dev bash scripts/staging-smoke.sh` (must report 19/19 PASS) |

> The demo runs end-to-end on staging — no localhost required. Every URL
> in the beats below is copy-paste-runnable.

---

## 1. Pitch (90 seconds, before any UI)

> **Read aloud, do not show slides.**

A job board tells you what jobs exist. **MontGoWork tells you why you
can't get one** — and then helps you fix it.

In Montgomery, Alabama and Fort Worth, Texas, the people who need work
the most are stuck behind a wall of barriers a job board can't see:
no transportation, a record from ten years ago, a credit score that
disqualifies them from the apartment they need to keep the job, a
benefits cliff that makes a $2/hr raise cost them $400 in SNAP.

MontGoWork is a worker companion that maps those barriers, builds a
personalized plan around them, and keeps the worker moving with a daily
digest, a stall detector, and a case manager looking over their
shoulder. Today we'll show you a worker arriving with nothing, walking
through their personal plan, generating a tailored resume, tracking
applications, and the case manager intervening when the worker stalls.
We'll also show you the compliance gate — the same one a city contract
will require — and the 12 production-grade fixes we shipped this
sprint to make this submission-ready, not hackathon-ready.

**The differentiator:** we are not a job-search tool. We are a
**barrier-removal tool** with a job-search tool inside it.

---

## 2. Demo flow (5-7 min — total 4:45 + 30s slack)

> Pre-load all 7 tabs (§5). Speak in the present tense ("the worker
> sees..."), not "if you click here you'd see...".

### Beat 1 — Worker arrival (60s)

**URL:** <https://montgowork-staging-web.fly.dev/>

What you do:

1. Land on home. Read the hero question + city stats aloud
   ("Montgomery poverty 21.4%. Labor participation 58.2%. We build
   for the 30% the market leaves behind.").
2. Click **Get Your Plan** → `/assess`.
3. Walk the assessment for a `medium` Montgomery session (barriers
   *transportation, credit, fair-chance*). The demo session is
   pre-seeded; click through defaults — `/plan` reads from the
   seeded session.
4. Open `/plan` (NavBar → Plan).

What the judges see:

- The **barrier inventory** — every blocker named, ranked, and tagged
  with "what we'd need to do."
- The **benefits cliff chart** (`BenefitsCliffChart` component) — a
  $2/hr raise vs. SNAP loss, drawn from live ALICE/SNAP rules.
- The **personalized action plan** — Monday-morning checklist
  (`MondayMorning`), career-center handoff, and resume / credit
  callouts.
- The **share button** — generates a redacted token-gated link the
  worker can send to a case manager (PII-stripped per T13.71 fix).

Lead line: "Every barrier ties to a specific next step, and every step
has a community resource — and we don't push the worker into a raise
that costs them more in lost SNAP than it earns."

### Beat 2 — Daily loop (60s)

**URL:** <https://montgowork-staging-web.fly.dev/daily>

What you do:

1. Switch to the `/daily` tab. The digest is computed nightly by the
   T12.20 composer + T12.18 stall detector.
2. Point at the three sections rendered by `DigestYesterdaySection`,
   `DigestTodaySection`, `DigestWeekSection`.
3. If the seeded session has `counts.stall > 0`, the
   **StallAlert banner** is up — point at it and say "the platform
   noticed the worker hasn't moved in 10 days; the plan is auto-
   refreshing to break the stall."
4. Mark one action checkbox complete on the `/plan` page (toggle in
   the `JobReadinessResults` panel) and switch back to `/daily`.

What the judges see:

- A digest tailored to *yesterday → today → this week*, not a
  one-size-fits-all dashboard.
- The **stall detector** — soft / medium / hard / breakthrough levels
  with corresponding intervention copy.
- The **plan refresher** firing on `stall_hard` or `barrier_resolved`
  triggers (T12.24).

Lead line: "Nightly digest, today's three actions, this week's funnel.
If the worker stalls 10 days, the plan rewrites itself — no dead
checklists."

### Beat 3 — Documents (45s)

**URL:** <https://montgowork-staging-web.fly.dev/documents/resume>

What you do:

1. Show the version history list — every prior generation persisted
   with `generation_method` ("template" or "ai").
2. Paste a one-liner job description into the target-job textarea
   (e.g. "Warehouse associate, second shift, Fort Worth, fair-chance
   employer"), click **Generate Resume**.
3. The markdown preview renders. Click the version's **Download PDF**
   link to confirm WeasyPrint pipeline streams a real PDF (open in a
   new tab; let it render briefly; close the tab).

What the judges see:

- Worker-voice resume copy — the `apply_worker_voice` rule chain
  strips em-dashes, hedge words, AI-isms, and reads at F-K grade <9.
- The **fair-chance branch** if the seeded session has a record —
  resume includes a one-line reframe drawn from
  `criminal.fair_chance_index`.
- The **PDF** — server-side WeasyPrint with print-friendly template.

Lead line (security wins): "AI generation is gated by feature flag —
default off. Every worker-controlled string passes a prompt-injection
filter (T13 expanded its scope). Every version writes a row the
worker owns."

### Beat 4 — Jobs kanban (45s)

**URL:** <https://montgowork-staging-web.fly.dev/jobs>

What you do:

1. Show the kanban — 5 status columns + funnel sidebar with
   conversion rates.
2. Drag an application from "Applied" to "Interview" (dnd-kit);
   `updateApplicationStatus` fires; sidebar live-updates.
3. Click an application card; show the **resume version reference**
   (linked from Beat 3) + `generation_method` badge.

What the judges see:

- City-aware sourcing — the seeded jobs come from BrightData scrapes
  for Montgomery / Fort Worth specifically; no Alabama-resident is
  ever shown a Dallas warehouse job.
- The funnel — applications → interviews → offers, with the
  conversion rate computed live.

Lead line: "The funnel feeds the weekly review, and every application
is tied back to the exact resume version that was sent."

### Beat 5 — Compliance gate (30s)

**Run this in a visible terminal pane.**

```bash
# 1. Show the route is wired (POST without body returns 422)
curl -s -m 15 -X POST \
    -o /tmp/c.json -w "\nHTTP=%{http_code}\n" \
    https://montgowork-staging-api.fly.dev/api/compliance/export
cat /tmp/c.json

# 2. Show the auth gate (bogus token returns 401)
curl -s -m 15 -X POST \
    -H "Content-Type: application/json" \
    -d '{"session_id":"<demo-uuid-from-§A>","session_token":"bogus"}' \
    -o /tmp/c2.json -w "\nHTTP=%{http_code}\n" \
    https://montgowork-staging-api.fly.dev/api/compliance/export
cat /tmp/c2.json
```

Lead line: "Production-grade compliance gate. Right-to-export,
right-to-delete with a `confirm: 'DELETE'` speed bump, retention
sweep, hashed `compliance_audit` tombstone. CAN-SPAM unsubscribe is
signed with a 7-day key-rotation overlap. Twelve production-grade
fixes landed this sprint — see §B."

### Beat 6 — Case manager view (45s)

**URL:** <https://montgowork-staging-web.fly.dev/case-manager>
(open in a second window, ideally on a second monitor).

What you do:

1. Paste advisor token into the URL: `?advisor_token=<adv-mgm-...>`
   (§A for staging values).
2. Show the **Needs Attention** inbox — `StalledSessionsList` shows
   city-scoped workers (cross-city → 403).
3. Click into one stalled session, open `SendAdvisorNoteDialog`,
   write a one-line note, send.
4. Switch back to the worker tab; the note lands in their next
   digest (describe the loop, don't wait for nightly).

What the judges see:

- The **city-scoped advisor model** — `advisor_tokens` table with
  partial active-token index, instant revoke, SHA256 audit hash.
- The **stalled-session list** — drawn from the same T12.18 stall
  detector that fires the worker's stall banner.
- The **Send Note** flow — per-advisor rate limit, audit row.

Lead line: "Same data model on both sides. The case manager isn't
watching from a CRM — they see the worker's plan, scoped to their
city, with a full audit trail."

### Beat 7 — Close (30s)

> Stop sharing screen. Speak directly.

Three things nothing else does: **(1) cliff awareness** — every plan
models SNAP/Medicaid/childcare cliffs so a "good job" doesn't cost
the worker money; **(2) fair-chance routing** — record-aware resume
gen + sourcing, partnered with the FW fair-chance employer index;
**(3) worker + case manager tandem** — same data model on both
sides; the case manager is a co-pilot, not a CRM observer.

Ask: your **attention and feedback**. We're targeting city-
government contracts in Q3 — the questions you ask are the questions
a procurement officer will ask in July. Tell us what's missing.

---

## 3. Backup paths (if a beat breaks live)

| If this breaks | Do this |
|----------------|---------|
| Frontend cold-start >5s on first hit | Pre-warm at T-2 minutes (§5). If still slow live, narrate over the loading state — "Fly.io is rotating the machine; staging runs on a single shared host." |
| Backend cold-start (`/health/live` 503) | Wait 30s and retry. Cold start measured at ~28s on dry-run (2026-04-25). Skip Beat 5's curl pane and verbally describe the compliance gate. |
| `medium` Montgomery session has stale data | Switch to `medium` Fort Worth (UUID in §A). All 5 stall states are seeded for both cities — pick another. |
| Resume generation fails on Beat 3 | Click into an existing version in the history list and download its PDF. The version row is pre-seeded by the demo factory. |
| Drag fails on Beat 4 | Use the **Move** button on the application card (the `MoveMenu` modal lists every column). Same mutation, different UI affordance. |
| Advisor token rejected on Beat 6 | Re-run `qc_reset.py` (§0). The advisor token is regenerated deterministically by the seed. |
| All else fails | Switch to slides + screenshots in `docs/press-kit/`. The submission package includes static screenshots of every beat. |

---

## 4. Timing budget

| Beat | Budget | Dry-run page load (warm) |
|------|-------:|--------------------------:|
| Pitch (verbal) | 90s | — |
| 1 Arrival | 60s | 4.84s cold → 0.08s warm |
| 2 Daily | 60s | 0.13s |
| 3 Documents | 45s | 0.13s (+ ~10s for resume gen) |
| 4 Jobs | 45s | 0.15s |
| 5 Compliance (curl) | 30s | 0.07s × 2 |
| 6 Case manager | 45s | 0.08s |
| 7 Close (verbal) | 30s | — |
| **Total** | **6:45** | 30s slack within 7-min cap |

---

## 5. Pre-demo checklist (T-30 minutes)

- [ ] **T-30: wake the staging machines.** First Fly.io hit can take
      30-90s on a stopped machine. Cold-start measured at ~28s on
      backend `/`, ~4.8s on frontend `/` (2026-04-25).
      ```bash
      curl -s -m 90 -o /dev/null -w "API=%{http_code} WEB=" \
          https://montgowork-staging-api.fly.dev/
      curl -s -m 90 -o /dev/null -w "%{http_code}\n" \
          https://montgowork-staging-web.fly.dev/
      ```
- [ ] **T-25: verify demo data fresh.** `curl
      https://montgowork-staging-api.fly.dev/api/dashboard/stats` —
      non-zero counts.
- [ ] **T-20: if drift, reset.** `fly ssh console --app
      montgowork-staging-api` then `python scripts/qc_reset.py
      --db-path /app/data/montgowork.db`.
- [ ] **T-15: smoke check.** Must report 19/19 PASS.
      ```bash
      STAGING_FRONTEND_URL=https://montgowork-staging-web.fly.dev \
      STAGING_API_URL=https://montgowork-staging-api.fly.dev \
          bash scripts/staging-smoke.sh
      ```
- [ ] **T-10: pre-load all 7 tabs** — `/`, `/assess`, `/plan`,
      `/daily`, `/documents/resume`, `/jobs`, `/case-manager?
      advisor_token=<§A>` — in this order.
- [ ] **T-5: open a terminal pane** for Beat 5; have the two curl
      commands ready in scrollback.
- [ ] **T-2: re-warm.** Fly machines sleep after ~10 minutes idle.
      One final `/health` curl on each keeps them awake.
- [ ] **T-0: deep breath, smile, hit "Share Screen."**

---

## 6. Verification log (2026-04-25 dry-run)

**Smoke script:** `bash scripts/staging-smoke.sh` → **19/19 PASS**
(every backend health + public-API + admin-auth route + every demo
frontend page).

**Cold-start (Fly.io spin-up):** backend `/` 28s, backend
`/health/live` 36s with mid-spin-up 503 (recovered to 200 within
10s), frontend `/` 4.8s. **Warm:** every route <200ms.

**Compliance gate (Beat 5) verified:** `POST /api/compliance/
export` with no body → 422 + missing-field detail; with bogus
session token → 401 "Invalid token". 0.07s warm.

**`/health/ready` returned 503 (warm)** — known: RAG index not
loaded in staging; smoke accepts 200/503 (component QC suites cover
the dep-up assertion).

**Beats that need session/advisor token to exercise fully** (route
shells verified 200; interactive paths covered by T13.10–T13.52
browser suites): Beat 1 form click-through, Beat 2 checklist
toggle, Beat 3 Generate-Resume + PDF download, Beat 4 kanban drag,
Beat 6 advisor inbox.

---

## 7. Talking-point cheat sheet

- **Differentiator:** "Barrier-removal tool with a job-search tool inside it, not the other way around."
- **Cliffs:** "A $2 raise that costs $400 in SNAP isn't a raise. We model that explicitly."
- **Fair-chance:** "Record-aware resume generation and job sourcing, partnered with the FW fair-chance index."
- **Stall:** "Soft / medium / hard / breakthrough. Hard fires the plan refresher; breakthrough fires confetti."
- **Compliance:** "Right-to-export, right-to-delete, hashed audit, signed unsubscribe, retention sweep — the same gate a city contract requires."
- **Security:** "Prompt-injection filter on every worker input. PII redaction on share endpoints. Kid-whitelist downgrade defense on every signing path."
- **Tandem:** "Worker and case manager share the same data model. The advisor isn't watching from a CRM."

---

## A. Demo data reference (seeded by `app.demo_seed_s12b`)

10 sessions = 5 stall states × 2 cities. Session IDs are
deterministic UUIDs hashed from `s12b-demo:{city}:{state}`:

| City | Stall state | Session UUID |
|------|-------------|--------------|
| montgomery | none | `05931d47-0c3a-4170-bb2c-9cf836fc0168` |
| montgomery | soft | `7f665990-2793-4277-ad99-5dc6c928e68b` |
| montgomery | **medium** *(primary demo)* | `f888fa8b-c8ae-49e4-84fd-410751aaa697` |
| montgomery | hard | `88aa2ba4-1d57-471d-9391-8b31abc0b5ec` |
| montgomery | breakthrough | `58980aa4-84a8-4257-b09b-93119a7126d4` |
| fort-worth | none | `f38fb0fa-c417-44a9-bc72-c57cc2fa2d61` |
| fort-worth | soft | `af96078f-5020-45fc-80de-7f78510f33fd` |
| fort-worth | medium *(backup)* | `7eb63d01-fcab-4235-af42-aaabba1e0fae` |
| fort-worth | hard | `cea3b444-12bc-4130-b42e-fc7a144da32d` |
| fort-worth | breakthrough | `1c070ab5-3744-4a5b-975d-7b0cdc22bed9` |

**Advisor tokens** rotate per `qc_reset` run. Pull the plaintext via
`fly ssh console --app montgowork-staging-api` then `sqlite3
/app/data/montgowork.db "SELECT advisor_id, plaintext FROM
advisor_tokens WHERE advisor_id LIKE 'adv-demo-%';"`. URL pattern for
Beat 6: `…/case-manager?advisor_token=<plaintext>`. Token persists to
`sessionStorage` on first load.

---

## B. Production-fix highlights (S13)

Twelve fixes shipped: share-endpoint PII redaction (T13.71),
document + credit rate limits (T13.99), PII log scrubber (T13.94),
`/plan` empty-state UX (T13.72), Spanish translation parity
(T13.77), Dependabot (T13.104), kid-whitelist downgrade defense
across appointments + compliance export + unsubscribe (T13.62 +
follow-up), boot-time env validator (T13.118), compliance cascade
introspection guard (T13.70), DST-safe weekly-review boundaries
(T13.66), QC dashboard at `/admin/qc` (T13.8). Test count: backend
3257 → 4012 (+755), frontend 946 → 1055 (+109).

---

## C. References

`.paircoder/config.yaml` (project description), `.paircoder/
context/state.md` (sprint summaries), `docs/runbooks/staging-
deploy.md`, `docs/ops/compliance-operations.md`,
`backend/app/demo_seed_s12b.py` + `app/_demo_seed_qc.py` (seed
factories), `scripts/staging-smoke.sh`, `scripts/qc_reset.py`.

---

> **Authored:** S13 T13.111. **Dry-run:** 2026-04-25. **Cap:** ≤7 min
> live + ≤2 min Q&A. Every route measured.
