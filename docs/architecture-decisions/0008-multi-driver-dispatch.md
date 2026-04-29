# ADR-0008: Multi-driver dispatch pattern (4 parallel worktrees per phase)

- **Date:** 2026-04-21
- **Sprint:** W1 (Visual Rebirth — Foundation)
- **Status:** Accepted

## Context

The visual rebirth (W1–W5) had a hard deadline (HackFW 2026 submission,
May 2). Each phase had ~10 distinct workstreams (camera choreography,
chapter copy, accessibility, edge states, life layers, OG generation,
press kit, video, deploy, Spanish parity, etc.). A single sequential
driver would have taken 6+ weeks. We had 4.

We needed parallel work that didn't step on each other. Git branches
alone aren't sufficient — Claude agent threads can't share a working
tree.

## Decision

Run 4 parallel Claude-driven worktrees per phase. Each worktree:

- Branches off the sprint branch at the same SHA
- Owns a constrained scope (life layers, edge states, accessibility,
  maximization)
- Pushes to its own branch (`w{N}-driver-{a|b|c|d}/{slug}`)
- Reports back with a structured final report (gates, files, tests,
  Spotlights)
- Gets souji-merged into the sprint branch sequentially

The dispatch pattern:

| Driver | Lane | Examples |
|---|---|---|
| **Driver A** | Foundation / scaffold | Camera, chapters, copy |
| **Driver B** | Edge states / fallbacks | Reduced motion, mobile, ES parity |
| **Driver C** | Quality / a11y / readiness | Lighthouse, AAA, deploy |
| **Driver D** | Maximization / integration | Per-chapter OG, polish, Spotlights |

Each driver receives a **dispatch** (the KANSEI brief) describing:

- Identity + mission + scope
- Critical (P0) tasks + acceptance criteria
- Constraints (don't touch X, don't regress Y)
- Output contract (gates, Spotlights, reports)
- Authority (push to own branch; do not modify sibling branches)

Drivers are intelligent teammates. They write tests first, ship working
code, run gates, file Spotlight inventions for long-term force
multiplication.

SubagentStop hooks feed token telemetry into the calibration engine,
which learns how long each driver class takes for each task class.

## Consequences

**Enables.**

- 4× parallel velocity per phase.
- Worktree isolation prevents merge conflicts on the same files.
- Calibration engine learns over time → future dispatches are
  accurately scoped.
- Spotlight inventions accumulate (each driver files ≥3-7 per phase
  → 12-28 per phase → ~75 across W1-W5).
- Driver-D maximization closes integration gaps that no single
  driver would have caught.

**Forecloses.**

- Cannot share unfinished work across drivers in a phase. Each
  driver completes their lane and pushes; cross-driver coordination
  happens in the dispatch (P0 ordering) or post-merge.
- Cannot run more than 4 simultaneously without cognitive overload
  on the operator (the human reviewing dispatches + reports).

**Cost.**

- Operator (Shawn) writes 4 dispatches per phase + reviews 4 reports.
- Souji-merge step per phase (sequential merging, often with
  `--ours` for state.md to avoid trivial conflicts).
- Calibration engine + telemetry infrastructure (one-time
  PairCoder build).

## Alternatives considered

1. **Single sequential driver.** Rejected — would have missed the
   hackathon deadline.
2. **Two parallel drivers.** Half the velocity, half the dispatch
   overhead. Rejected because most phases have 4 distinct lanes that
   are genuinely parallel.
3. **8+ parallel drivers.** Too much operator overhead; lanes
   get redundant; calibration noise increases.

## What we'd revisit

If a phase has fewer than 4 genuinely parallel lanes, run 2-3
drivers instead of 4. The pattern is not "always 4"; it's "as many
as the phase decomposition supports".

If the operator becomes the bottleneck (writing dispatches + reviewing
reports), invest in PairCoder dispatch templates + auto-review
helpers.

## See also

- [`docs/visual-rebirth-briefs.md`](../visual-rebirth-briefs.md) — per-sprint briefs
- `.paircoder/feedback/calibration.json` — driver calibration ledger
- `.claude/agents/` — driver / navigator / reviewer role definitions
- `.paircoder/context/state.md` — historical record of dispatches
