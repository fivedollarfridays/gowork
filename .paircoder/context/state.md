# Current State

> Last updated: 2026-03-05

## Active Plan

**Plan:** plan-2026-03-a11y-and-demo
**Type:** chore
**Title:** Phase 6: Accessibility + Final Polish
**Status:** In Progress
**Current Sprint:** 10

## Previous Plans

- plan-2026-03-docs-and-readme (Complete, 5/5 done -- Sprint 9)
- plan-2026-03-export-and-polish (Complete, 4/4 done -- Sprint 8)
- plan-2026-03-brightdata-live-jobs (Complete, 6/6 done -- Sprint 7)
- plan-2026-03-demo-killer-frontend (Complete, 10/10 done -- Sprint 5)
- plan-2026-03-plan-2026-03-implementation (Complete, 9/9 done -- Sprint 4)
- plan-2026-03-test-coverage (Complete, 4/4 done -- Sprint 3)
- plan-2026-03-plan-2026-03-review-fixes (Complete, 3/3 done)
- plan-2026-03-module-skeletons (Complete, 7/7 done)

## Current Focus

Sprint 10: Accessibility + Final Polish. All 5 tasks complete.

## Task Status

### Sprint 10 -- Accessibility + Final Polish

| ID | Title | Priority | Complexity | Status | Depends On |
|----|-------|----------|------------|--------|------------|
| T10.0 | Semantic HTML -- headings, landmarks, form labels | P0 | 30 | done | -- |
| T10.1 | Keyboard nav -- tab order, focus in wizard | P0 | 25 | done | -- |
| T10.2 | ARIA -- live regions, async updates, button states | P0 | 25 | done | -- |
| T10.3 | Claude narrative polish -- demo-quality prompts | P1 | 20 | done | -- |
| T10.4 | Demo script -- Maria scenario, click path | P1 | 15 | done | T10.0-T10.3 |

**Total: 5 tasks, 115 complexity points (5/5 done)**

## What Was Just Done

### Session: 2026-03-05 - T10.4 Demo Script

- Created `docs/demo-script.md` (222 lines) with complete demo walkthrough
- Maria persona: 34, Montgomery, ZIP 36104, 4 barriers (credit/transport/childcare/criminal_record), credit 580
- 8-section click-by-click path: landing -> basic info -> barriers -> credit -> review -> plan -> jobs -> export
- Talking points per screen with what to say and what to highlight
- Timing targets: 3 minutes total, 15-30s per section
- Pre-demo checklist: servers, API keys, seed data, browser zoom
- Q&A prep: 5 likely questions with answers
- Fallback plan for demo failures (backend down, AI fails, etc.)

### Session: 2026-03-05 - T10.2 ARIA Live Regions + Async Updates

- Added `aria-live="polite"` to loading spinner in assess/page.tsx (profile analysis)
- Added `role="alert"` to error message in assess/page.tsx
- Added `aria-busy="true"` and `aria-label="Loading your plan"` to PlanSkeleton in plan/page.tsx
- Added `role="alert"` to error state container and narrative error in plan/page.tsx
- Added `aria-live="polite"` wrapper around narrative loading card in MondayMorning.tsx
- Added `aria-label="Generating PDF, please wait"` to PlanExport button during generation
- Added `role="alert"` to PlanExport error message
- Added `aria-live="polite"` to EmailExport success message ("Plan sent to...")
- Added `role="alert"` to EmailExport error message
- Added `role="alert"` to credit/page.tsx mutation error
- Added contextual `aria-label` to WizardShell Previous/Next buttons (e.g., "Go to step 2: Barriers")
- Created 8 new tests: 4 WizardShell ARIA tests, 2 PlanExport ARIA tests, 2 EmailExport ARIA tests, 2 MondayMorning ARIA tests
- All 75 frontend tests pass, build clean, all files within arch limits

### Session: 2026-03-05 - T10.1 Keyboard Nav and Focus Management

- Added programmatic focus management to WizardShell: when step changes, focus moves to the step content container so keyboard users don't lose their place
- Added `useRef<HTMLDivElement>` for step content container, `tabIndex={-1}` on CardContent (allows programmatic focus without adding to tab order), `outline-none` to suppress focus ring on container
- Added `useEffect` watching `currentStep` with `setTimeout(0)` for DOM readiness; skips focus on initial mount via `hasMountedRef` flag
- Added `aria-current="step"` to the active step indicator circle in the nav
- Created 7 tests in `WizardShell-a11y.test.tsx`: aria-current on mount, aria-current not on non-current steps, aria-current moves on navigation, tabIndex=-1 presence, no focus on mount, focus on next, focus on back
- All 73 frontend tests pass, build clean

### Session: 2026-03-05 - T10.3 Claude Narrative Polish

- Rewrote SYSTEM_PROMPT in `backend/app/ai/prompts.py`: persona is now "caring, experienced workforce navigator at the Alabama Career Center in Montgomery." Includes Montgomery-specific context (M-Transit, Alabama Career Center, Montgomery Job Corps, GreenPath Financial, local employers). Style rules: short paragraphs, 2-3 sentences, direct "you" address, no emojis. JSON response format: summary (max 250 words Monday Morning narrative) + key_actions (3-5 concrete steps).
- Rewrote USER_PROMPT_TEMPLATE: frames the task as sitting across from the resident. Includes barriers, qualifications, plan data placeholders. Instructs Monday morning pep talk, specific resource/job references, M-Transit for transportation barriers, concrete key_actions with places and deadlines.
- Rewrote `build_fallback_narrative()` in `backend/app/ai/client.py`: replaced robotic "Based on your assessment, you have barriers in:" with empathetic, Montgomery-specific template. Opening acknowledges courage. Monday morning next step references first matched contact or Alabama Career Center. Job titles woven naturally. Empty-data fallback still warm and actionable.
- Refactored fallback into 4 helper functions (`_fallback_opening`, `_fallback_next_step`, `_fallback_jobs_sentence`, `_build_fallback_summary`) to satisfy arch check function length limits.
- Added 13 new tests in `tests/test_prompts.py` (persona, tone, Montgomery context, style, JSON format, no emojis, template placeholders, rendering).
- Added 7 new tests in `tests/test_fallback_narrative.py` (empathetic tone, Montgomery references, natural job mentions, natural contacts, empty plan warmth, specific actions, no emojis).
- All 255 tests pass (235 original + 20 new). All arch checks clean. No function signature changes.

## What's Next

1. Commit/push/PR for Phase 6 (Sprint 10 complete)

## Blockers

None.
