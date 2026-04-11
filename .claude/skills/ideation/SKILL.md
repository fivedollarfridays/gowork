---
name: ideation
description: Transforms a rough idea into a sprint-level structured brief for /draft-backlog. Operates only at sprint scope — cross-task dependencies, file collisions, Cx budget, priority ordering, and AC templates — never per-task implementation detail, which is /pc-plan's responsibility during engage. Uses bpsai-pair validate, budget, arch, and query tools at wider scope than /pc-plan uses them.
---

# Ideating

## Scope Rule (read first)

This skill operates at the **sprint level only**. Per-task implementation detail is `/pc-plan`'s job during `bpsai-pair engage`. If the output contains per-task file-level implementation strategy, per-task exhaustive grep of the codebase, or per-task arch checks, stop — that work will be redone by `/pc-plan` and thrown away.

The division of labor:

| Decision | Owner | Why |
|---|---|---|
| What tasks should exist | ideation | `/pc-plan` only sees one task at a time |
| Cross-task dependencies | ideation | `/pc-plan` can't see siblings |
| File collisions across parallel tasks | ideation | `/pc-plan` is scoped to its task |
| Sprint Cx budget | ideation | Sum of per-task estimates |
| Priority ordering (P0/P1/P2) | ideation | Engage's cut-list if budget overflows |
| Scope boundaries (in/out) | ideation | Sprint-level decision |
| Per-task implementation strategy | `/pc-plan` | Not ideation's job |
| Per-task file-level arch check | `/pc-plan` | Not ideation's job |
| Per-task test identification | `/pc-plan` | Not ideation's job |
| Wave scheduling + parallelism | `engage` | Not ideation's job |
| Retry on failure | `engage` | Not ideation's job |

**Same tools, different scopes.** Ideation calls `bpsai-pair arch check`, `budget estimate`, `validate`, `query` — but at cross-task scope. `/pc-plan` calls the same tools per-task. That's not duplication; it's layered use.

## When to Use

When the user has a rough idea and wants to turn it into a sprint. Sits between "I want to build X" and `/draft-backlog`. The user invokes this with `/ideation <idea>` or by describing what they want to build.

The output is a structured brief that becomes the input to `/draft-backlog`. Better input = fewer review rounds + cleaner engage runs.

## Input

A rough idea. Can be a sentence, a paragraph, a bullet list, or a file path to notes. Examples:
- "add OCR receipt scanning"
- "rip out the old auth middleware and replace with JWT"
- "sprint to harden the API against the OWASP top 10"
- A path to a design doc or feature request

If the idea is vague ("make it faster", "improve the API"), ask one clarifying question before running discovery. Don't guess.

## Steps

### Step 0: Fail fast — validate repo state

Run these first. If any fail, stop and fix before continuing — ideation is wasted if the repo is in a bad state.

```bash
bpsai-pair validate                              # repo structure + context consistency
bpsai-pair doctor                                # environment health
bpsai-pair status                                # current branch, last action, stale tasks
bpsai-pair query tasks --status in_progress     # check for conflicting open work
```

Flag any `in_progress` tasks that touch files the new sprint will also touch. These are conflict risks and must be resolved (marked done, explicitly blocked, or scoped away) before the sprint starts.

### Step 1: Sprint-level surface discovery (parallel with Step 2)

Not a full codebase inventory — `/pc-plan` will handle per-file discovery during engage. Ideation only needs enough to size the sprint and identify subsystems the idea touches.

```bash
# How big is the codebase? Which subsystems does the idea touch?
find . -type d -maxdepth 2 -not -path '*/.*' -not -path '*/node_modules/*' -not -path '*/venv/*'

# Counts by top-level directory (for budget scaling, not inventory)
find . -type f \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' \) -not -path '*/venv/*' -not -path '*/node_modules/*' | cut -d'/' -f2 | sort | uniq -c | sort -rn | head -10

# Test-to-source ratio (signal for test infra maturity)
find . -name 'test_*.py' -o -name '*.test.*' 2>/dev/null | wc -l
```

### Step 2: Cross-task constraint detection (not per-task inspection)

Use the bpsai-pair tooling, but only at sprint scope. The goal is to find constraints that **span multiple tasks** or **block parallelization** — things `/pc-plan` structurally cannot see because it's scoped to one task.

```bash
# Sprint-level arch constraints — only flag violations that:
#   (a) block a task until a prerequisite refactor runs, OR
#   (b) span multiple tasks (e.g., one file that two parallel tasks need to split)
bpsai-pair arch check . 2>&1 | grep -v "test" | head -30

# Oversized files in the feature's path that will GROW under this sprint.
# Per-task splits are /pc-plan's job; ideation flags cross-task structural issues.
find . \( -name '*.py' -o -name '*.ts' \) -not -path '*/venv/*' -not -path '*/node_modules/*' -not -name 'test_*' | while read f; do
    lines=$(wc -l < "$f"); [ "$lines" -gt 300 ] && echo "$lines $f"
done | sort -rn | head

# TODOs / FIXMEs only in the feature's path AND that need to become their own tasks.
# Not a general cleanup hunt — /pc-plan catches task-local TODOs.
grep -rn 'NotImplementedError\|# TODO\|# FIXME\|# HACK' --include='*.py' --include='*.ts' <feature-path-roots>
```

**The key question for each finding:** does this constraint matter across tasks, or only within one task? If only within one task, `/pc-plan` will handle it. Drop it from the brief.

### Step 3: Identify candidate tasks and estimate budget

Break the idea into candidate tasks. For each task, use `bpsai-pair budget estimate` to get a Cx number instead of guessing.

```bash
# Per-task Cx estimate — feed the task's intended file list and change scope
bpsai-pair budget estimate --task "<short task description>" --files "<file list>"

# Sprint total — sum of per-task estimates
bpsai-pair budget status    # current remaining budget check
```

For each task, also assign:
- **Priority P0/P1/P2** — P0 = ships or fails the sprint, P1 = should ship, P2 = cut if budget overflows. This ordering is engage's cut-list.
- **Task ID** — follow backlog's naming convention (`T{sprint}.{seq}`)

### Step 4: Build the dependency graph + file collision matrix

Every task needs explicit `Depends on:` wiring. Phase structure in the brief is for humans; engage schedules waves from the dependency graph.

For each pair of tasks that would run in parallel (no dependency between them), check whether they touch the same file. If yes, either:
- Serialize them (add a `Depends on:` edge)
- Split one into a parent prep task + dependent child tasks

```bash
# File collision check — for each parallel-wave pair, intersect file lists
# If intersection is non-empty, flag collision in the brief
```

Output the dependency graph explicitly in the brief — each task must have a `Depends on:` line (or `Depends on: none` for sprint-entry tasks).

### Step 5: Write AC templates per task category

Don't hand-write every AC. Group tasks by category and apply templates. `/pc-plan` will refine per task during engage.

**Migration task template (JSON/JSONL → SQLite, or similar):**
- [ ] No file path references remain
- [ ] Old constants/imports removed
- [ ] CRUD function signatures preserved (backward-compat for callers)
- [ ] Seed fixture helper added to `tests/conftest.py`
- [ ] Existing tests pass with fixture swap
- [ ] `ruff check` clean on touched files

**Schema task template:**
- [ ] Migration runs clean on fresh DB
- [ ] Migration idempotent (re-run safe via PRAGMA check)
- [ ] Column/table verifiable via `PRAGMA table_info`
- [ ] No data loss on existing rows
- [ ] Round-trip test

**Refactor task template:**
- [ ] `bpsai-pair arch check <file>` passes
- [ ] Line count does not grow
- [ ] Behavior unchanged (existing tests still green)

**Integration gate template:**
- [ ] Full test suite green
- [ ] `ruff check .` clean
- [ ] `bpsai-pair arch check .` → no new violations
- [ ] `.paircoder/context/state.md` reconciled
- [ ] PR pushed, CI green

### Step 6: Synthesize the brief

Using findings from steps 0-5, produce a structured brief. This becomes the input to `/draft-backlog`.

**Format:**

```markdown
# Feature Brief: [Title]

## Idea
[One paragraph restating the user's idea with clarity, including scope boundaries]

## Codebase Context
- **Stack:** [language, framework, key deps]
- **Size:** [top-level directory counts, test-to-source ratio]
- **Current sprint:** [what's active, what just shipped]
- **Conflicting in-progress tasks:** [from Step 0, or "none"]

## Sprint-Level Constraints
- **Cross-task arch constraints:** [only those spanning multiple tasks]
- **Oversized files that will grow:** [files that need a split task as prerequisite]
- **TODOs that become tasks:** [only those blocking the feature path]
- **Cross-task contract edges:** [what Task A produces that Task B consumes]

## Tasks
[Per task, include ALL of:]
- **ID:** T{sprint}.{seq}
- **Title:** brief description
- **Cx:** from `bpsai-pair budget estimate`
- **Priority:** P0/P1/P2
- **Depends on:** [list of task IDs or "none"]
- **Files:** [exhaustive list — file exclusivity matters for parallel waves]
- **AC template:** [category — migration/schema/refactor/gate]
- **Custom AC:** [task-specific additions beyond the template]

## Dependency Graph
[Tasks grouped by dependency depth. Each wave = tasks with the same depth.
 Engage schedules waves from this structure via --max-parallel.]

## File Collision Matrix
[For each parallel wave: intersection check. "None" or "Task A / Task B / file".]

## Sprint Budget
- **Total Cx:** [sum of per-task estimates]
- **Task count:** [N]
- **P0 count / P1 count / P2 count:** [for engage cut-list planning]

## Integration Points
[Cross-task only — what Task A produces that Task B consumes.
 Per-task integration is /pc-plan's job.]

## Out of Scope
[Explicit boundaries. This prevents scope creep during engage
 and gives /pc-plan a clear stop line.]
```

### Step 7: Deliver

End the response with:

```
Brief ready. To generate the backlog:

  /draft-backlog <paste or reference the brief above>
```

## Decision Rules

- **If the idea is vague** ("make it faster", "improve the API"): ask one clarifying question before running discovery. Don't guess.
- **If the codebase is empty/new** (< 5 source files): skip Step 2, the brief is mostly "What Needs to Be Built" with minimal constraint detection.
- **If the idea touches > 50% of the codebase**: flag as a refactor, suggest splitting into multiple sprints.
- **If Step 0 finds in-progress tasks conflicting with the proposed sprint**: stop and flag — ask whether to resolve the conflict or scope around it.
- **If two parallel tasks touch the same file**: never leave it for engage to discover. Either serialize them (add a `Depends on:` edge) or split one.
- **If `bpsai-pair budget estimate` is unavailable or returns nothing**: fall back to comparing against the budget on the most recent completed sprint of similar shape.

## What This Skill Does NOT Do

- **Per-task implementation strategy** — `/pc-plan`'s job during engage
- **Per-task file-level arch check** — `/pc-plan`'s job during engage
- **Per-task TODO inspection** — `/pc-plan`'s job during engage
- **Per-task test file identification** — `/pc-plan`'s job during engage
- **Wave scheduling / parallelism** — `engage`'s job
- **Write the backlog** — `/draft-backlog`'s job
- **Validate the backlog** — `/prepare-to-engage`'s job
- **Review code** — `/reviewing-code`'s job
- **Analyze review output** — `/analyzing-review-report`'s job

This skill's only job is to produce a sprint-level brief that makes `/draft-backlog` produce a better backlog on the first pass, and gives `/pc-plan` a clear per-task starting point during engage.

**Never recommend `bpsai-pair engage --skip-planning`.** `/pc-plan` is the enforcement layer that catches ideation errors. Skipping it trades correctness for tokens — a bad trade.
