# QC Suite Authoring Guide

This directory holds `.qc.yaml` browser-driven QC suites for MontGoWork. Suites
are run by the `divona` agent (interactive Chrome, broad coverage, author-time)
and by Playwright headless (CI gate, top-five critical paths only — see T13.129).

Reference:
- **Step type reference:** `.claude/agents/divona.md`
- **Environment profiles:** `.paircoder/qc/config.yaml`
- **Suite template:** `.paircoder/qc/suites/_template.qc.yaml`

---

## Suite naming

- Filename: `<role>-<flow>.qc.yaml`, all kebab-case.
- `suite_id` inside the file must match the filename minus `.qc.yaml`.
- Roles: `worker`, `advisor`, `admin`, `unauth`.
- Flow: short verb phrase. Examples:
  - `worker-onboarding.qc.yaml`
  - `worker-apt-reminder-cancel.qc.yaml`
  - `advisor-send-note.qc.yaml`
  - `admin-flag-toggle.qc.yaml`
  - `unauth-unsubscribe-get.qc.yaml`

One suite per user journey. Suites that exceed ~8 scenarios should be split.

---

## Demo-session requirements

Every suite must run against deterministic demo data. Sessions are seeded by
`bpsai-pair qc reset` (T13.3), which calls `demo_seed_s12b.py` plus the S13
extension (T13.2).

- Reference sessions by their stable IDs from `config.yaml.test_credentials`,
  never hardcode them.
- If your suite needs state the seed doesn't provide, extend the seed —
  do **not** mutate state in `setup:` and rely on it sticking. Setup steps
  are for navigation, not data plumbing.
- Cross-city flows must run against both Montgomery and Fort Worth sessions
  (declare both as `scenarios:` or as parameterized runs once that's wired).

---

## Cleanup contract

- The seed → reset cycle is the canonical isolation boundary. A suite must
  leave the DB in a state another suite can run against, or call `qc reset`
  itself.
- Default: rely on the runner's between-suite reset; leave `cleanup:` empty.
- Only add suite-level cleanup when your suite intentionally creates state
  another suite needs to find — and document why.
- **Never** delete demo sessions. The seed assumes they exist.

---

## Steps vs. assertions

A step does one of two things:

| Kind | Step types | Purpose |
|------|------------|---------|
| **Action** | `navigate`, `click`, `fill`, `wait` | Drive the browser |
| **Assertion** | `verify`, `check_console` | Produce pass/fail evidence |

Every scenario must end with at least one assertion. A scenario with only
actions proves nothing — the runner will still report PASSED if the actions
ran without throwing, which is misleading.

Good shape: `navigate → fill × N → click → wait → verify → check_console`.

---

## Tags

Canonical tag list (extend in PRs, don't proliferate ad-hoc):

| Tag | Meaning |
|-----|---------|
| `worker` / `advisor` / `admin` / `unauth` | Primary role |
| `happy-path` / `error-path` / `edge-case` | Path category |
| `mutates` | Modifies data; **excluded** in `prod` profile |
| `destroys-prod-data` | Hard-destructive; excluded in `staging` + `prod` |
| `requires-auth` | Won't run on `prod` (no creds there) |
| `slow` | Suite takes >60s; excluded from PR-gated CI |
| `flaky` | Known-flaky; excluded from gating runs until fixed |
| `i18n` | Exercises both EN and ES |
| `a11y` | Includes accessibility assertions |

Use `restrictions.skip_tags` in `config.yaml` to exclude tags per environment.

---

## Divona vs. Playwright — when to use which

Two QC runners share this directory of suites. Pick the right one for the job:

| Runner     | Use when                                                                                            |
|------------|-----------------------------------------------------------------------------------------------------|
| divona     | Authoring a new suite (interactive, visible Chrome); broad coverage; flows that need human visual judgment; ad-hoc triage |
| Playwright | CI gate (every PR); top-five critical paths; headless, fast, parallel; deterministic regression detection |

### Source-of-truth contract

The `.qc.yaml` file is **canonical** — it documents the flow, the demo session
ID, the assertions, and the expected outcomes. Divona reads it directly.

Playwright equivalents live in `frontend/e2e/<suite-id>.spec.ts` and are
maintained in **lockstep** with the `.qc.yaml`. When you change a `.qc.yaml`,
you must update the matching Playwright spec in the same PR (and vice versa).
Drift between the two is a CI failure once T13.125 lands.

### Adding a new Playwright spec

1. Create `frontend/e2e/<suite-id>.spec.ts` mirroring the `.qc.yaml`.
2. Wrap the suite in `test.describe("@critical <suite-name>", ...)` so the
   PR-gating CI run picks it up via `--grep "@critical"`.
3. Use the same demo session IDs from `.paircoder/qc/config.yaml`
   (`test_credentials.*`); never hardcode.
4. Run locally to confirm: `cd frontend && npm run test:e2e -- --grep "@critical"`.
5. Keep the spec under 200 lines; split into multiple specs if the flow
   grows beyond that (one user journey per file).

Only the **top-five** critical paths should carry `@critical`. Broader
coverage stays in divona where author intent and visual judgment matter.

### `@critical` index — demo-gating Playwright specs

These six specs gate the hackathon demo. Each mirrors one beat of the
demo script; if any one fails on a PR, the demo path is broken. Run all
of them with `cd frontend && npm run test:e2e -- --grep "@critical"`.

| # | Spec file (under `frontend/e2e/`) | Demo beat | Notes |
|---|-----------------------------------|-----------|-------|
| 1 | `worker-onboarding.spec.ts` | Beat 1: home → assess | No auth required |
| 2 | `worker-daily-loop.spec.ts` | Beat 2: tokenized digest | Worker session via URL params |
| 3 | `worker-resume-llm-off.spec.ts` | Beat 3: template-mode resume | Asserts version-history wiring; no mutation |
| 4 | `worker-jobs-kanban.spec.ts` | Beat 4: jobs board | Render + columns; drag covered by divona |
| 5 | `worker-compliance-export.spec.ts` | Beat 5: data export | API-level (`request.post` / `request.get`) |
| 6 | `advisor-login-inbox.spec.ts` | Beat 6: advisor inbox | `?advisor_token=...` URL param auth |

Demo-session credentials live in `frontend/e2e/_demo_session.ts` —
deterministic IDs + tokens derived from the seed in
`backend/app/demo_seed_s12b.py` + `_demo_seed_qc.py`. Refresh those
constants if either seed module's hash inputs change.

---

## How to invoke

### Via divona (interactive, full coverage)

Through the Claude Code orchestrator:

```
/run-qc <suite-id>
```

Or direct agent dispatch when authoring a new suite:

> "Run `worker-onboarding.qc.yaml` against `dev` and report findings."

Divona will load the suite, check preconditions, run scenarios step-by-step in
Chrome, and write a JSON report to `.paircoder/qc/runs/`.

### Via Playwright (headless, CI gate)

Set up once per checkout (T13.129 lands the harness):

```
cd frontend && npm install && npx playwright install chromium
```

Then run the PR-gating subset:

```
cd frontend && npm run test:e2e -- --grep "@critical"
```

Or run everything:

```
cd frontend && npm run test:e2e
```

Other modes:
- `npm run test:e2e:headed` — watch tests in a visible browser
- `npm run test:e2e:debug` — step through tests in Playwright Inspector

Playwright auto-starts `next dev` on port 3000 (see
`frontend/playwright.config.ts.webServer`); reuses an existing dev server when
one is already running locally. CI starts a fresh server (`reuseExistingServer:
false` when `CI` is set).

### Smoke-load (just verify a suite parses)

```
python -c "import yaml; yaml.safe_load(open('.paircoder/qc/suites/<file>.qc.yaml'))"
```

---

## Authoring checklist

Before opening a PR with a new suite:

- [ ] Filename matches `suite_id`
- [ ] Every scenario ends with at least one assertion
- [ ] Demo session IDs come from `config.yaml`, not hardcoded
- [ ] Tags from the canonical list (or PR adds the new tag here)
- [ ] Suite parses (`yaml.safe_load` smoke test above)
- [ ] Runs green at least once locally before merge
- [ ] Cross-city if applicable (Montgomery + Fort Worth)
- [ ] Cross-locale if applicable (EN + ES)

---

## When NOT to write a `.qc.yaml`

- Logic that's testable as a unit — write a Python/TS unit test instead.
- Flows that don't exercise the browser — backend-only flows go in `backend/tests/`.
- One-off debugging — use the Chrome DevTools, don't pollute the suite directory.
