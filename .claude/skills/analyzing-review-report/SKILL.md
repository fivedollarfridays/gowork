---
name: analyzing-review-report
description: Analyzes bpsai-pair review branch output by cross-referencing findings against actual code and task state. Classifies each finding as real blocker, bookkeeping-only, already resolved, or defer-to-next-sprint. Outputs a filtered report that becomes input to /draft-backlog, breaking the review-loop pattern.
---

# Analyzing Review Report

## When to Use

After `bpsai-pair review branch` returns findings and before running `/draft-backlog`. The reviewer's job is to find everything; this skill's job is to figure out what's actually left. Prevents the loop pattern where stale statuses and already-fixed code get re-flagged as blockers round after round.

The user invokes this with `/analyzing-review-report` or by asking to analyze the review report. The review output is either pasted in the conversation or in the most recent `bpsai-pair review branch` output.

## Input

The review report from `bpsai-pair review branch`, containing P0/P1/P2 findings from reviewer, security-auditor, and cross-module-reviewer agents.

## Steps

### 1. Gather Context (parallel)

Run all three in parallel — they're independent reads:

```bash
# What's the current branch and diff surface?
git diff main...HEAD --stat

# What tasks exist and what are their statuses?
find .paircoder/tasks -name '*.task.md' -exec grep -l 'status: in_progress\|status: pending' {} \;

# What's the current state?
cat .paircoder/context/state.md
```

### 2. Analyze Each Finding

For every P0, P1, and P2 finding in the report, run this triage:

**a) Check if the code fix already exists:**
```bash
# Search for the fix the finding describes
grep -rn '<pattern from finding>' <file from finding>
git log --oneline --all -- <file from finding> | head -5
```

**b) Check if the task is actually done:**
```bash
# If finding references a task ID, check its real status
cat .paircoder/tasks/<task-id>.task.md | grep -E 'status:|acceptance_criteria'
```

**c) Check if it's a bookkeeping-only issue:**
- Task status says `in_progress` but code is implemented and tests pass
- Plan file has wrong `status:` field
- State.md has stale entries

**d) Check if it's noise:**
- Finding references a file that hasn't changed since last review
- Finding is about deleted code that's already gone from the tree
- Finding duplicates another finding in the same report

### 3. Classify Each Finding

Assign one of four categories:

| Category | Meaning | Action |
|----------|---------|--------|
| **BLOCKER** | Real code/security issue, not yet fixed | Must fix before merge |
| **BOOKKEEPING** | Code is done, status/metadata is stale | Flip status, no code change |
| **RESOLVED** | Finding is wrong — code already handles this | Strike from report |
| **DEFER** | Legitimate improvement, not a merge blocker | Move to next sprint backlog |

### 4. Output the Filtered Report

Produce a structured report in this format:

```markdown
# Review Analysis: [Branch Name]

**Source:** `bpsai-pair review branch` output from [date]
**Original findings:** X P0, Y P1, Z P2
**After analysis:** A blockers, B bookkeeping, C resolved (noise), D deferred

## Real Blockers (must fix)

| # | Severity | Finding | File | Why it's real |
|---|----------|---------|------|---------------|
| 1 | P0       | ...     | ...  | ...           |

## Bookkeeping Only (status flip)

| # | Original Severity | Finding | Task | What to flip |
|---|-------------------|---------|------|--------------|
| 1 | P0                | ...     | ...  | ...          |

## Resolved (noise — struck from report)

| # | Original Severity | Finding | Evidence |
|---|-------------------|---------|----------|
| 1 | P1                | ...     | Code at file:line handles this |

## Deferred to Next Sprint

| # | Original Severity | Finding | Why defer |
|---|-------------------|---------|-----------|
| 1 | P1                | ...     | Architectural improvement, not blocker |

---

## Recommended /draft-backlog Input

> Only the Blockers and Bookkeeping items above. Do NOT backlog
> Resolved or Deferred items. Deferred items go into a separate
> sprint-N+1 parking lot below.

### Closure tasks (feed to /draft-backlog):
[List only BLOCKER and BOOKKEEPING items with suggested task IDs and Cx]

### Sprint N+1 parking lot (not for this backlog):
[List DEFER items as future sprint candidates]
```

### 5. Validate the Reduction

Report the noise ratio:

```
Noise reduction: X of Y findings removed (Z%)
- Resolved (false positives): N
- Bookkeeping (no code needed): N
- Deferred (not this sprint): N
Remaining actionable items: N
```

If the noise ratio is above 50%, flag it — the review scope may need narrowing (e.g., delta-only review instead of full branch diff).

## Decision Rules

When classification is ambiguous, apply these tiebreakers:

1. **If code exists and tests pass → BOOKKEEPING**, not BLOCKER. The reviewer sees stale status; the code is fine.
2. **If finding is about documentation/skill files only → DEFER** unless it's actively misleading users right now.
3. **If finding requires `git filter-repo` or other destructive ops → BLOCKER** but flag as needing a human decision (scrub vs accept-risk).
4. **If finding duplicates a prior-round finding that was already addressed → RESOLVED** with reference to the fix commit.
5. **If finding is about thread safety, future-proofing, or "what if" scenarios → DEFER** unless there's a concrete failure mode today.

## Anti-Patterns This Skill Prevents

- **Backlisting the whole report** — generates 15+ tasks, starts another review round
- **Re-flagging done work** — stale `in_progress` status triggers phantom P0s
- **Scope creep through cross-module discovery** — each fix exposes another code path
- **Deferral avoidance** — treating every P1 as "must fix before merge" when it's sprint N+1 work
