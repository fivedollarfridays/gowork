# PR Description Generation Guide

This document describes how the SUBMIT phase of souji-sweeping generates
a comprehensive PR description from the branch diff and pipeline results.

## Data Sources

The PR description is assembled from these sources:

1. **Git log** -- commit messages since divergence from main
2. **Diff stat** -- files changed, insertions, deletions
3. **Test results** -- pass counts from Phase 4 (VERIFY)
4. **Review findings** -- summary from Phase 1 (REVIEW)
5. **Security scan** -- results from Phase 5 (SECURE)
6. **Remediation log** -- any CI fixes from Phase 8.5

## Gathering Data

```bash
# Branch name
BRANCH=$(git branch --show-current)

# Commit summary (one-liners)
COMMITS=$(git log main..HEAD --format="- %s")

# Changed files with stats
STAT=$(git diff main...HEAD --stat)

# File list only
FILES=$(git diff main...HEAD --name-only)

# Diff summary (insertions/deletions)
DIFF_SUMMARY=$(git diff main...HEAD --shortstat)

# Test results (capture from Phase 4 output)
# Backend: "X passed, Y failed"
# Frontend: "X passed, Y failed"
```

## PR Title

Generate from the branch name or most recent meaningful commit:

```bash
# Option 1: From branch name
echo "$BRANCH" | sed 's/-/ /g; s/\b\(.\)/\u\1/g'

# Option 2: From the first commit on the branch
git log main..HEAD --format="%s" | tail -1
```

Keep the title under 70 characters. Use imperative mood.

## PR Body Template

```markdown
## Summary
<2-3 sentences describing what this branch accomplishes>

## Changes

### Added
- <new files or features>

### Modified
- <changed files with brief description>

### Fixed
- <bugs fixed, issues resolved>

## Test Results

| Suite | Result | Count |
|-------|--------|-------|
| Backend (pytest) | Pass | <N> |
| Frontend (vitest) | Pass | <N> |

## Review Summary

| Severity | Found | Fixed |
|----------|-------|-------|
| P0 (blockers) | <N> | <N> |
| P1 (quality) | <N> | <N> |
| P2 (improvements) | <N> | <N> |

## Security

- Secrets scan: Clean
- Dependency audit: <Clean / N warnings>

## Architecture

All modified files within limits:
- Lines: < 400 (source), < 600 (test)
- Functions: < 15/file (source), < 30/file (test)
- Function length: < 50 lines

## CI Remediation

<If no remediation was needed:>
CI passed on first push.

<If remediation was needed:>
CI required N remediation cycles:
1. <cycle 1 description>
2. <cycle 2 description>

## Checklist

- [x] All tests passing
- [x] Architecture limits respected
- [x] No debug statements
- [x] No hardcoded secrets
- [x] Branch up to date with main
- [x] Security scan clean
```

## Generating the Summary Section

Analyze the commit log and diff to produce a human-readable summary:

1. **Count commits by type** (feat, fix, refactor, test, docs)
2. **Identify the primary change** (what the branch is FOR)
3. **Note secondary changes** (cleanup, refactors done along the way)
4. **Mention scope** (which modules/components were affected)

## Handling Existing PRs

If a PR already exists for the branch:

```bash
# Check for existing PR
EXISTING=$(gh pr list --head "$BRANCH" --json number -q '.[0].number')

if [ -n "$EXISTING" ]; then
  # Update existing PR
  gh pr edit "$EXISTING" --body "$BODY"
  echo "Updated PR #$EXISTING"
else
  # Create new PR
  gh pr create --title "$TITLE" --body "$BODY"
fi
```

## PR Labels

If the repository uses labels, apply automatically based on pipeline results:

```bash
# Add labels based on content
gh pr edit "$PR_NUM" --add-label "tested,reviewed,security-scanned"
```

## Linking to Issues and Tasks

If commit messages contain task IDs (TASK-XXX, T2.1, TRELLO-XX),
include them in the PR body as references:

```bash
# Extract task IDs from commits
git log main..HEAD --format="%s" | grep -oE 'T[0-9]+\.[0-9]+|TASK-[0-9]+|TRELLO-[a-zA-Z0-9]+'
```
