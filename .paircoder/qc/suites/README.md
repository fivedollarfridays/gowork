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

### Via Playwright (headless, CI gate — once T13.129 lands)

```
cd frontend && npx playwright test --grep "@critical"
```

Playwright suites mirror a subset of `.qc.yaml` suites tagged `@critical`.
Authoring a `.qc.yaml` is the source of truth; the Playwright equivalent is
generated/maintained in lockstep.

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
