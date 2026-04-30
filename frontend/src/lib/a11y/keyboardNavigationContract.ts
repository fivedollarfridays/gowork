/**
 * keyboardNavigationContract — central source-of-truth Tab order on `/`.
 *
 * W4 Driver C Spotlight #1 (T4.C.8.1).
 *
 * # Why this exists
 *
 * Driver C's Playwright keyboard sweep walks the homepage Tab order and
 * asserts each focusable receives focus in sequence. Without a shared
 * contract, two things drift:
 *   1. The expected order itself (a future PR adds a button mid-header
 *      and silently changes the sequence the audit was looking for).
 *   2. The CSS selector used to identify each focusable (test pulls a
 *      `data-testid`, prod ships `aria-label` only, gap surfaces months
 *      later as a "test passes but real users hit a focus trap").
 *
 * This module exports ONE canonical array, used by the keyboard sweep AND
 * by any future a11y audit (W5 manual QA, lighthouse-budget-diff, etc).
 *
 * # Compound Lens
 *
 * - W4 today: Playwright e2e walks the order on `/`.
 * - W5: manual QA references the same array — "did each item get focus?"
 *   becomes a checklist driven from this constant.
 * - Future: per-route arrays (`DAILY_TAB_ORDER`, `JOBS_TAB_ORDER`) drop in
 *   alongside this one. The shared `FocusableEntry` shape keeps the
 *   ergonomics identical.
 *
 * # Selector strategy
 *
 * Each entry is a CSS selector against the live DOM, NOT a `data-testid`.
 * Real users don't have testids; the audit asserts what real users hit
 * (class names, aria attributes, links by href). When the production
 * markup changes, the selector breaks LOUDLY in CI rather than silently
 * passing on a synthetic testid.
 */

/** A single focusable element in the expected Tab order. */
export interface FocusableEntry {
  /** Stable id for the audit (`brand-mark`, `language-toggle`). */
  id: string;
  /** CSS selector against the rendered DOM. */
  selector: string;
  /** Human-readable label for failure messages and manual-QA scripts. */
  label: string;
}

/**
 * Expected Tab order on the homepage `/` from top of document down.
 *
 * Order rationale (matches `frontend/src/app/layout.tsx` mount order):
 *   1. SkipToContent — proudly visible on focus, MUST be first
 *   2. Header brand mark (Link to /) — first chrome focusable
 *   3. NavBar items (worker-companion routes, may be 0..N depending on
 *      role; the contract only pins entries the layout always renders)
 *   4. Mute toggle (header chrome)
 *   5. Language toggle (EN/ES)
 *   6. GitHub icon link (header chrome)
 *
 * Items inside `<main id="main">` (the Wall chapters' interactive
 * controls — slider in Ch6, "Apply" button in Ch10, etc.) are pinned by
 * per-chapter audits; this homepage contract covers the always-present
 * chrome.
 */
export const HOMEPAGE_TAB_ORDER: ReadonlyArray<FocusableEntry> = [
  {
    id: "skip-to-content",
    selector: "a.skip-to-content",
    label: "Skip to main content",
  },
  {
    id: "brand-mark",
    selector: "header a[href='/']",
    label: "GoWork brand mark (link to home)",
  },
  {
    id: "mute-toggle",
    selector: "header button[aria-label*='mute' i], header button[aria-label*='audio' i]",
    label: "Mute / unmute audio toggle",
  },
  {
    id: "language-toggle",
    selector: "header button[aria-label*='language' i], header button[aria-label*='idioma' i]",
    label: "Language toggle (EN / ES)",
  },
  {
    id: "github-link",
    selector: "header a[href*='github.com']",
    label: "GitHub repository link",
  },
];

/** Returns the contract length without exposing the raw array. */
export function expectedTabOrderLength(): number {
  return HOMEPAGE_TAB_ORDER.length;
}

/** Returns the entry at the given index, or undefined when out of range. */
export function selectorAt(index: number): FocusableEntry | undefined {
  if (index < 0 || index >= HOMEPAGE_TAB_ORDER.length) return undefined;
  return HOMEPAGE_TAB_ORDER[index];
}

/** Truthy guard for selector strings; rejects empty / whitespace-only. */
export function isFocusableSelector(selector: string): boolean {
  return typeof selector === "string" && selector.trim().length > 0;
}
