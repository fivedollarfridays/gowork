# Remediation Playbook -- CI Failure Patterns

This document catalogs common CI failure patterns and their surgical fixes for the REMEDIATE phase of souji-sweeping.

## Reading CI Logs

```bash
# Get the failed run ID
RUN_ID=$(gh run list --branch "$(git branch --show-current)" --status failure --limit 1 --json databaseId -q '.[0].databaseId')

# View failed logs (truncated)
gh run view "$RUN_ID" --log-failed 2>/dev/null | head -200

# View full logs for a specific job
gh run view "$RUN_ID" --log --job <job-id> 2>/dev/null | tail -100

# List all jobs in a run
gh run view "$RUN_ID" --json jobs -q '.jobs[] | "\(.name): \(.conclusion)"'
```

## Pattern 1: Python Test Failure

**Log signature:**
```
FAILED tests/test_module.py::test_function - AssertionError
```

**Diagnosis:**
```bash
# Run the specific failing test locally
py -3.12 -m pytest tests/test_module.py::test_function -v --tb=long

# Check if it's an import issue
py -3.12 -c "import module_under_test"
```

**Common causes:**
- Missing fixture or conftest.py not in PYTHONPATH
- Environment variable not set in CI (but set locally)
- Database state dependency (test ordering issue)
- Relative import that works locally but fails in CI working directory

**Fix pattern:**
1. Reproduce locally with `py -3.12 -m pytest` (not `python`)
2. Fix the root cause (not the symptom)
3. Run full suite locally before pushing

## Pattern 2: Frontend Test Failure (Vitest/Jest)

**Log signature:**
```
FAIL src/components/MyComponent.test.tsx
  Expected: "foo"
  Received: "bar"
```

**Diagnosis:**
```bash
# Run the specific test
npx vitest run src/components/MyComponent.test.tsx

# Check for missing env vars
grep -r "process.env\|import.meta.env" src/components/MyComponent.tsx
```

**Common causes:**
- Missing environment variable in CI
- Snapshot out of date
- CSS module mock not configured
- Window/document API not available in test runner

**Fix pattern:**
1. Update snapshot if intentional change: `npx vitest -u`
2. Mock browser APIs in test setup
3. Ensure `.env.test` or CI env vars match

## Pattern 3: Lint Failure (Ruff/ESLint)

**Log signature:**
```
ruff check: E501 line too long
eslint: error  Unexpected any  @typescript-eslint/no-explicit-any
```

**Diagnosis:**
```bash
# Python
ruff check . --select E,W,F --diff

# Frontend
npx eslint . --format compact 2>&1 | head -30
```

**Fix pattern:**
1. Auto-fix what can be auto-fixed: `ruff check . --fix`
2. Manually fix remaining issues
3. For line length, split long strings or extract variables
4. For type issues, add proper types instead of `any`

## Pattern 4: Type Check Failure (mypy/tsc)

**Log signature:**
```
error TS2345: Argument of type 'string' is not assignable to parameter of type 'number'
src/api/route.py:42: error: Incompatible return value type
```

**Diagnosis:**
```bash
# Python
py -3.12 -m mypy src/ --ignore-missing-imports 2>&1 | head -30

# TypeScript
npx tsc --noEmit 2>&1 | head -30
```

**Fix pattern:**
1. Add or correct type annotations
2. Use type narrowing (isinstance checks, type guards)
3. Never suppress with `# type: ignore` unless truly unavoidable

## Pattern 5: Build Failure

**Log signature:**
```
Module not found: Can't resolve './component'
ModuleNotFoundError: No module named 'package'
```

**Diagnosis:**
```bash
# Check if the import path is correct
find . -name "component.*" -not -path "./node_modules/*"

# Check if dependency is in requirements/package.json
grep "package" requirements.txt pyproject.toml package.json
```

**Fix pattern:**
1. Fix import path (case sensitivity matters on Linux CI)
2. Add missing dependency to requirements.txt or package.json
3. Check for circular imports

## Pattern 6: CI Configuration Issue

**Log signature:**
```
Error: Process completed with exit code 1.
Node.js 18 actions are deprecated.
```

**When this happens:** The failure is NOT in the code.

**Fix pattern:**
1. This is an infrastructure issue, not a code issue
2. Trip the circuit breaker -- report to user
3. Suggest updating `.github/workflows/*.yml`

## Remediation Decision Tree

```
CI failure detected
|
+-- Is it a test failure?
|   +-- YES: Reproduce locally, fix code, push
|   +-- NO: Continue
|
+-- Is it a lint/type failure?
|   +-- YES: Auto-fix if possible, manual fix if not, push
|   +-- NO: Continue
|
+-- Is it a build failure?
|   +-- YES: Check imports and dependencies, fix, push
|   +-- NO: Continue
|
+-- Is it an infrastructure/config issue?
|   +-- YES: Trip circuit breaker, report to user
|   +-- NO: Read full logs, diagnose, attempt fix
```

## Circuit Breaker Rules

The circuit breaker trips when:

1. **Same failure repeats** after a fix attempt (regression or wrong diagnosis)
2. **5 total cycles** reached without all-green
3. **Infrastructure failure** (not fixable by code changes)
4. **Flaky test detected** (passes locally, fails in CI intermittently)

When the breaker trips, output:

```
CIRCUIT BREAKER TRIPPED

Cycle:     N of 5
Failure:   <check name>
Pattern:   <which pattern from this playbook>
Last fix:  <what was attempted>
Diagnosis: <why it did not resolve>

Recommended action:
- <specific next step for the user>
```

## Commit Message Convention for Remediation

All remediation commits use this format:

```
fix(ci): <what was fixed>

Souji remediation cycle N/5.
<one-line explanation of root cause>
```

This makes remediation commits easy to identify in git log and
distinguishes them from feature work.
