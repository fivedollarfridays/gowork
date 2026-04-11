---
name: prepare-to-engage
description: Runs pre-flight checks and fixes before bpsai-pair engage. Resolves merge conflicts, commits dirty bookkeeping files, drops stale auto-stashes, validates the backlog, and outputs the ready-to-run engage command.
---

# Prepare to Engage

## When to Use

Before running `bpsai-pair engage <backlog>`. Fixes the issues that cause engage to fail at branch checkout so the user can copy-paste the engage command and go.

The user invokes this with `/prepare-to-engage` or by asking to prepare for engage. The backlog path comes from context — check `plans/backlogs/` for the target file, or ask if ambiguous.

## Steps

Run steps 1–3 in parallel (they're independent reads), then fix issues sequentially.

### 1. Resolve Unmerged Paths

```bash
git status
```

If unmerged files exist:

- `.paircoder/` files (state.md, store.db, task files): **auto-fix** with `--theirs` — engage regenerates these.
  ```bash
  git checkout --theirs <files> && git add <files>
  ```
- Source or test files: show the conflict diff and ask the user which version to keep. Do not auto-resolve these.

### 2. Clean the Working Tree

```bash
git diff --stat
git diff --cached --stat
```

The tree must be clean for engage to checkout its branch. Fix by category:

- **`.paircoder/` bookkeeping only** (state.md, store.db, task files, config): commit automatically.
  ```bash
  git add .paircoder/ && git commit -m "chore: pre-engage bookkeeping sync"
  ```
- **Source/test files staged or modified**: commit them with a descriptive message covering what changed.
  ```bash
  git add <files> && git commit -m "chore: pre-engage cleanup — <description>"
  ```
- **Untracked files in `.claude/skills/` or `.paircoder/`**: stage and include in the commit.
- **Untracked source files**: ask the user before staging.

### 3. Drop Stale Auto-Stashes

```bash
git stash list
```

`Auto-stash before containment checkpoint` entries accumulate across sessions and are never restored. **Drop all of them** without asking — they are machine-generated, not user work.

```bash
# Drop from highest index to lowest to avoid index shifting
git stash drop stash@{N}
```

If non-auto stashes exist (user-created `WIP on ...` entries), leave them alone.

### 4. Validate Target Branch

Derive branch from backlog filename: `engage/{backlog-stem}`.

```bash
git branch --list 'engage/<backlog-stem>'
```

- Already on it: no action needed.
- Exists, different branch: tree must be clean (step 2 handles this).
- Doesn't exist: engage will create it.

### 5. Validate Backlog File

```bash
ls -la <backlog-path>
```

Must exist and be non-empty. If missing, check `plans/backlogs/` for similar names and suggest corrections.

### 6. Gate Check

```bash
bpsai-pair status
```

Look for license errors, config issues, or blocked state. Report any blockers to the user.

### 7. Dry-Run Validation

Once all issues are fixed, run the dry-run to confirm the backlog parses correctly:

```bash
bpsai-pair engage <backlog-path> --dry-run
```

- If it passes: proceed to step 8.
- If it fails: diagnose the error (usually backlog formatting), fix it, and re-run until it passes.

### 8. Output the Engage Command

Once the dry-run passes, end the response with the command:

```
Ready to engage:

  bpsai-pair engage <backlog-path>
```

**This is mandatory.** The engage command must always be the last thing in the response.
