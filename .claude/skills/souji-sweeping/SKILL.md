---
name: souji-sweeping
description: Orchestrates the full branch-to-merge pipeline. Runs code review, surgical fixes, architecture simplification, test verification, security audit, PR submission, CI monitoring, and automated failure remediation in a single invocation. Integrates reviewing-code, implementing-with-tdd, architecting-modules, and finishing-branches skills into a nine-phase pipeline with a circuit-breaker-guarded CI remediation loop. Produces a green, merge-ready PR or a structured failure report.
---

# Souji Sweeping -- Branch Purification Pipeline

> **souji** (掃除) -- the Japanese practice of cleaning as discipline.
> One sweep. Zero debris. Merge-ready.

## When to Use

- Branch is code-complete and needs to ship
- Sprint is finished and all tasks are done
- User says "clean up and ship this branch"
- Before a demo, hackathon submission, or release deadline
- After `bpsai-pair review branch` returns findings that need bulk remediation

## Prerequisites

Before invoking this skill, verify:

```bash
# Branch exists and has commits ahead of main
git log main..HEAD --oneline | head -5

# Tests can run (dependencies installed)
py -3.12 -m pytest --co -q 2>/dev/null | tail -1

# gh CLI authenticated
gh auth status
```

If any prerequisite fails, fix it before proceeding.

## Pipeline Overview

```
RECON --> REVIEW --> FIX --> SIMPLIFY --> VERIFY --> SECURE --> FINISH --> SUBMIT --> WATCH+REMEDIATE --> READY
```

| Phase | Agent/Skill | Purpose | Blocking? |
|-------|-------------|---------|-----------|
| 0. RECON | navigator | Assess branch scope and headroom | Yes |
| 1. REVIEW | reviewing-code | Audit all changed files | Yes |
| 2. FIX | implementing-with-tdd | Surgical fixes for findings | Yes |
| 3. SIMPLIFY | architecting-modules | Enforce file/function limits | Yes |
| 4. VERIFY | driver | Run full test suites | Yes |
| 5. SECURE | security-auditor (Laverna) | Secrets and vulnerability scan | Yes (P0 only) |
| 6. FINISH | finishing-branches | Clean commits, rebase | Yes |
| 7. SUBMIT | driver | Create PR with auto-description | Yes |
| 8. WATCH | driver | Monitor CI checks | Yes |
| 9. REMEDIATE | implementing-with-tdd | Fix CI failures, loop to WATCH | Circuit-breaker |

## Phase 0: RECON -- Branch Assessment

Assess the branch before touching anything. Establishes a baseline.

```bash
# 1. Identify the diff surface
git diff main...HEAD --stat
git diff main...HEAD --name-only > /tmp/souji-changed-files.txt

# 2. Count the scope
git log main..HEAD --oneline | wc -l   # commits ahead
wc -l < /tmp/souji-changed-files.txt   # files changed

# 3. Architecture headroom check on ALL changed source files
# (Skip test files, config files, and non-code assets)
for f in $(grep -E '\.(py|ts|tsx|js|jsx)$' /tmp/souji-changed-files.txt | grep -v __pycache__ | grep -v node_modules); do
  if [ -f "$f" ]; then
    lines=$(wc -l < "$f")
    echo "$lines $f"
  fi
done | sort -rn | head -20
```

**Decision gate:** If any source file exceeds 350 lines, flag it for SIMPLIFY.
If the branch has zero commits ahead of main, abort -- nothing to sweep.

Record the baseline:
- Number of files changed
- Files approaching limits (>200 lines)
- Files exceeding limits (>400 lines)

## Phase 1: REVIEW -- Code Audit

Apply the **reviewing-code** skill methodology against the branch diff.

```bash
# See full diff
git diff main...HEAD

# Check for debug artifacts
git diff main...HEAD | grep -nE "print\(|console\.log|debugger|breakpoint|pdb"

# Check for hardcoded values
git diff main...HEAD | grep -nE "localhost|127\.0\.0\.1|hardcoded|TODO|FIXME|HACK"

# Check for secrets
git diff main...HEAD | grep -inE "password|secret|api.?key|token.*=.*['\"]"
```

Produce findings in the standard format:

- **P0**: Blocks merge (broken tests, security issues, crashes)
- **P1**: Fix before merge (quality issues, missing types, dead code)
- **P2**: Improvements (naming, documentation, minor refactors)

Group findings by file. Count totals. If zero findings, skip to Phase 4 (VERIFY).

## Phase 2: FIX -- Surgical Remediation

For each finding from Phase 1, apply fixes using **implementing-with-tdd** methodology.

**Order:** P0 first, then P1, then P2.

**Rules:**
1. Fix ONLY what was flagged. Do not rewrite working code.
2. For each fix, write or update a test that covers the specific issue.
3. Run the relevant test file after each fix to confirm green.
4. Group related fixes into a single commit per file or per logical change.

```bash
# After each fix, verify locally
py -3.12 -m pytest tests/path/to/relevant_test.py -x -q

# After all P0 fixes, run full backend suite
py -3.12 -m pytest tests/ -q --tb=short
```

**Skip condition:** If Phase 1 found zero issues, skip this phase entirely.

## Phase 3: SIMPLIFY -- Architecture Compliance

Apply the **architecting-modules** skill to all changed files.

```bash
# Check every changed source file against architecture limits
for f in $(grep -E '\.py$' /tmp/souji-changed-files.txt | grep -v __pycache__); do
  if [ -f "$f" ]; then
    bpsai-pair arch check "$f"
  fi
done
```

**Limits (from architecture.md):**

| Metric | Source | Test |
|--------|--------|------|
| Lines (error) | 400 | 600 |
| Lines (warning) | 200 | 400 |
| Functions/file | 15 | 30 |
| Function length | 50 | 50 |
| Imports/file | 20 | 40 |

For violations:
- Extract helper functions to `_helpers.py` or `_utils.py`
- Split large files using hub-and-spoke pattern
- Move shared fixtures to `conftest.py`

After each extraction, run tests to confirm zero regressions.

## Phase 4: VERIFY -- Full Test Suites

Run ALL test suites. Both backend and frontend.

```bash
# Backend (Python)
py -3.12 -m pytest tests/ -q --tb=short

# Frontend (if applicable -- check for vitest/jest config)
if [ -f "vitest.config.ts" ] || [ -f "vitest.config.js" ]; then
  npx vitest run
elif [ -f "jest.config.js" ] || [ -f "jest.config.ts" ]; then
  npx jest --ci
fi
```

**If tests fail:**
1. Identify the failing test(s) and root cause
2. Loop back to Phase 2 (FIX) for those specific failures
3. Re-run VERIFY after fixes
4. Maximum 3 verify-fix loops. If still failing after 3, report and halt.

**Pass condition:** Zero test failures in both backend and frontend.

## Phase 5: SECURE -- Security Scan

Invoke **security-auditor** (Laverna) methodology on the branch diff.

```bash
# Scan for secrets in staged/committed code
git diff main...HEAD | grep -inE \
  "password\s*=|secret\s*=|api.?key\s*=|token\s*=|BEGIN.*PRIVATE|AWS_|OPENAI_"

# Check for .env files that should not be committed
git diff main...HEAD --name-only | grep -iE '\.env|credentials|secrets'

# Check dependency files for known issues
if [ -f "requirements.txt" ]; then
  pip-audit -r requirements.txt 2>/dev/null || echo "pip-audit not available"
fi
```

**Severity handling:**
- Critical/High findings: HALT. Report to user. Do not proceed.
- Medium/Low findings: Log as warnings, continue pipeline.

## Phase 6: FINISH -- Branch Preparation

Apply **finishing-branches** skill methodology.

```bash
# 1. Ensure branch is up to date with main
git fetch origin main
git merge origin/main --no-edit || echo "CONFLICT: manual resolution needed"

# 2. Clean up commit history if needed
# (Do NOT rebase interactively -- just ensure clean state)
git log main..HEAD --oneline

# 3. Verify no merge conflicts remain
git diff --check
```

**If merge conflicts exist:** Report the conflicting files and halt.
The user must resolve conflicts manually, then re-invoke souji-sweeping.

## Phase 7: SUBMIT -- Create Pull Request

Generate the PR using branch diff analysis.

```bash
# 1. Gather PR content
BRANCH=$(git branch --show-current)
TITLE=$(git log main..HEAD --format="%s" | tail -1)
CHANGED=$(git diff main...HEAD --stat)
COMMIT_LOG=$(git log main..HEAD --format="- %s" | head -20)

# 2. Push branch
git push origin "$BRANCH" -u

# 3. Create PR (see reference/pr-template.md for body format)
gh pr create --title "$TITLE" --body "$(cat <<'EOF'
## Summary
<auto-generated from commit log and diff analysis>

## Changes
<changed files summary>

## Test Results
- Backend: <pass count> passing
- Frontend: <pass count> passing
- Coverage: <if available>

## Security
- Secrets scan: Clean
- Dependency audit: <status>

## Checklist
- [x] All tests passing
- [x] Architecture limits respected
- [x] No debug statements
- [x] No hardcoded secrets
- [x] Branch up to date with main
EOF
)"
```

**If a PR already exists** for this branch, update it instead:

```bash
gh pr edit --title "$TITLE" --body "$BODY"
```

Record the PR number and URL for Phase 8.

## Phase 8: WATCH -- CI Monitoring

Monitor CI checks on the newly created PR.

```bash
# Wait for checks to start (brief pause, then poll)
PR_NUM=$(gh pr view --json number -q .number)

# Check status
gh pr checks "$PR_NUM" --watch --fail-fast 2>/dev/null || \
  gh pr checks "$PR_NUM"

# Alternative: poll run status
gh run list --branch "$(git branch --show-current)" --limit 3
```

**Outcomes:**
- All checks pass --> proceed to Phase 9 (READY)
- Any check fails --> proceed to Phase 8.5 (REMEDIATE)
- Checks pending after 10 minutes --> report status, suggest user wait

## Phase 8.5: REMEDIATE -- CI Failure Loop

**Circuit breaker: maximum 5 remediation cycles.**

For each failed check:

```bash
# 1. Identify the failed run
RUN_ID=$(gh run list --branch "$(git branch --show-current)" --status failure --limit 1 --json databaseId -q '.[0].databaseId')

# 2. Read failure logs
gh run view "$RUN_ID" --log-failed 2>/dev/null | head -100

# 3. Identify the exact failure
# Parse the log output for:
#   - Test failures (assertion errors, import errors)
#   - Lint failures (ruff, eslint)
#   - Build failures (type errors, missing deps)
#   - Deployment failures (config issues)
```

**Remediation rules:**
1. Apply the minimal fix for the specific CI failure
2. Write or update a test if the fix is behavioral
3. Run local verification (Phase 4 commands) before pushing
4. Commit with message: `fix(ci): <description of what failed>`
5. Push and loop back to WATCH

```bash
# After fix
git add <fixed-files>
git commit -m "fix(ci): <description>"
git push

# Loop back to WATCH
gh pr checks "$PR_NUM"
```

**Circuit breaker triggers:**
- 5 consecutive remediation cycles with no progress
- Same failure repeating after fix attempt
- Failure requires environment/infrastructure change (not code)

When circuit breaker trips, produce a failure report:

```
SOUJI HALTED -- Circuit breaker after N remediation cycles

Failed check: <check name>
Last failure: <error summary>
Attempts: N/5

Files modified during remediation:
- <file list>

Recommended manual action:
- <specific guidance>
```

## Phase 9: READY -- Merge-Ready Report

All CI checks are green. Produce the final report.

```
============================================================
  SOUJI COMPLETE -- Branch Purified
============================================================

  Branch:    <branch-name>
  PR:        <PR-URL>
  Status:    All checks passing

  Pipeline Summary:
  - Review:     <N findings> (P0: X, P1: Y, P2: Z)
  - Fixed:      <N issues resolved>
  - Simplified: <N files refactored>
  - Tests:      <backend count> backend, <frontend count> frontend
  - Security:   Clean
  - CI:         All green (remediation cycles: N)

  The PR is merge-ready.
============================================================
```

## Abort Conditions

The pipeline halts immediately on:
1. **Zero commits** ahead of main (nothing to sweep)
2. **Merge conflicts** with main that require manual resolution
3. **Critical security finding** (secrets in code, critical CVE)
4. **Circuit breaker** on CI remediation (5 failed cycles)
5. **User interruption** (Ctrl+C or explicit stop)

On halt, report what was completed, what failed, and what remains.

## Skill Integration Map

| Phase | Primary Skill | Agent |
|-------|---------------|-------|
| RECON | -- | navigator |
| REVIEW | reviewing-code | reviewer (Nayru) |
| FIX | implementing-with-tdd | driver |
| SIMPLIFY | architecting-modules | driver |
| VERIFY | -- | driver |
| SECURE | -- | security-auditor (Laverna) |
| FINISH | finishing-branches | reviewer (Nayru) |
| SUBMIT | -- | driver |
| WATCH | -- | driver |
| REMEDIATE | implementing-with-tdd | driver |

## Quick Invocation

```bash
# Full pipeline (default)
# User says: "run souji-sweeping" or "clean up and ship this branch"

# Skip review if already reviewed
# User says: "run souji-sweeping, skip review -- already reviewed"
# Start from Phase 3 (SIMPLIFY)

# PR already exists, just watch CI
# User says: "run souji-sweeping from WATCH"
# Start from Phase 8
```

## Reference Documents

For detailed phase instructions beyond this overview, see:
- `reference/remediation-playbook.md` -- CI failure patterns and fixes
- `reference/pr-template.md` -- PR description generation guide
