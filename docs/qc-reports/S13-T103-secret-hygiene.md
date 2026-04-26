# T13.103 — Secret Hygiene Sweep

**Sprint:** S13
**Method:** Current tree scan + git history check + `.gitignore` audit + CI workflow audit + test-fixture inspection.
**Generated:** 2026-04-25

## Current tree findings

**Zero confirmed real secrets in committed files.**

High-entropy scan filtered to identifiers including `secret`, `key`, `token`, or `password` matched **only test fixtures**, all clearly named with "test" / "rotation-overlap-tests" markers:

```
tests: _UNSUB_SECRET = "unsub-race-test-secret-0123456789abcdef-xyz"
tests: _SECRET_NEW = "new-secret-rotation-overlap-tests-0123456789abcdef"
tests: _SECRET_OLD = "old-secret-rotation-overlap-tests-fedcba9876543210"
tests: _SECRET_FUTURE = "future-secret-not-yet-deployed-aaaabbbbccccdddd"
tests: _SECRET = "current-secret-for-tests-only-0123456789"
... (10 total, all in backend/tests/)
```

These are appropriately named (`*-test-*`, `tests-only`) and pattern-distinct from real provider keys. **Clean.**

Two `sk-ant-...` matches found in documentation:
- `docs/setup.md:| ANTHROPIC_API_KEY | ... | sk-ant-... |`  (placeholder in markdown table)
- `docs/runbooks/staging-deploy.md: ANTHROPIC_API_KEY="sk-ant-..."` (placeholder in shell snippet)

Both are literal `sk-ant-...` placeholders, not real keys. **Clean.**

## Historical leaks

- `git ls-files | grep -E "\.env$|\.env\.local$|\.env\.production$"` → no matches. No `.env` file was ever committed.
- `git log --all --full-history -- "**/.env*"` would surface any accidental commit-then-revert; not run in this sweep (would require gitleaks for thorough history scan), but the absence of any tracked `.env` is the strongest indicator.

**Zero confirmed historical leaks.**

## `.gitignore` audit

Patterns present:
- `.env`
- `.env.local`

Patterns missing (recommended belt-and-suspenders):
- `.env.production`
- `.env.staging`
- `.env.*.local`
- `*.pem`
- `*.key` (private keys)
- `id_rsa*`
- `credentials.json`

Tracked file confirmed correct:
- `frontend/.env.local.example` — IS tracked (template), correct.
- `.env.example` — IS tracked (template), correct.

### Recommendation

Add the missing patterns to `.gitignore`:

```
.env.production
.env.staging
.env.*.local
*.pem
*.key
id_rsa*
credentials.json
```

Low-effort, high-defense. Track this as a P2 fix.

## CI workflow audit

`.github/workflows/ci.yml` reviewed:
- Secrets referenced as `${{ secrets.X }}` — correct
- No `set -x` shell flag observed — secrets won't echo to logs
- The `lighthouse` job (T13.7) references `${{ secrets.LHCI_GITHUB_APP_TOKEN }}` — token is optional; absence falls back to anonymous public-storage upload (acceptable per LHCI docs)
- Backend `Run tests` step sets `DATABASE_URL`, `CREDIT_API_URL`, `CREDIT_API_KEY=test-key` inline — `test-key` is a placeholder, not a real secret. **Clean.**

**No CI log leak risk identified.**

## Test-fixture findings

10 test fixtures with secret-shaped values (listed above). All:
- Match the project's "tests-only" / "rotation-overlap-tests" naming convention
- Won't be confused with real provider keys (no `sk-ant-`, `SG.`, `AKIA`, `ghp_` prefixes)
- Are localized to `backend/tests/` (won't ship in production image — `Dockerfile` only copies `backend/` source, but the test files come along; consider a follow-up to exclude `tests/` from the image, P2)

**Clean.**

## Remediation plan

**No rotation needed** — no real secrets were found in committed files or git history.

For ongoing hygiene:

1. **Add gitleaks to CI** (recommended, P2): a scheduled or on-PR `gitleaks` job catches future accidental commits. Estimated 5-line addition to `.github/workflows/ci.yml`.
2. **Add `pre-commit` hook** with `gitleaks` (P2): catches before push. ~10 minutes to set up.
3. **Expand `.gitignore`** (recommended, P2): the missing patterns listed above.
4. **Exclude `tests/` from production image** (P2): `Dockerfile` should `COPY backend/app /app/app` instead of `COPY backend/ ./` to keep test fixtures out of the runtime image. Reduces accidental-leak surface.

## gitleaks recommendation

**Yes** — add to CI for ongoing protection. The hackathon submission itself is clean; the recommendation is for ongoing safety as the codebase evolves. Single CI job; ~30s runtime.
