/**
 * axeChapterRunner — reusable axe-core harness for chapter a11y tests.
 *
 * W3 Driver C Spotlight #1 (T3.24).
 *
 * # Why this exists
 *
 * Two W2 chapter test files (Chapter04Axe.test.tsx, EdgeStates.test.tsx)
 * each declare their own `AXE_OPTIONS` constant. W3 will add five more
 * chapter axe scans, plus W4 will add per-life-layer scans. Without a
 * shared harness, every test redefines the same four rule overrides and
 * the same severity filter, with subtle drift across files.
 *
 * # Compound Lens
 *
 * - W3 today: Ch10 axe scan (and skipped Ch6-9 placeholders).
 * - W3 souji: when A+B land Ch6-9 chapters, the placeholder un-skip
 *   reuses `runAxeOnChapter` directly — no per-driver inventiveness.
 * - W4: time-of-day life layers each get an axe smoke test that uses
 *   the same harness. Same input shape, same rule overrides, same gate.
 *
 * # Severity threshold
 *
 * The W3 brief sets the gate at "moderate or above" — minor a11y nits
 * (e.g., "the `<style>` tag has no `type` attribute") are not P0 and
 * we don't want to fail builds on them while moderate/serious/critical
 * are the real signal.
 */
import axe, {
  type AxeResults,
  type Result as AxeResult,
  type RunOptions as AxeRunOptions,
} from "axe-core";

/** Default ruleset used by every chapter axe scan. Disabled rules are
 *  the four where jsdom + chapter-isolation produce false positives. */
export const axeChapterRules: AxeRunOptions = {
  rules: {
    "color-contrast": { enabled: false },
    "meta-viewport": { enabled: false },
    "landmark-one-main": { enabled: false },
    region: { enabled: false },
  },
};

/** Severity threshold — anything at this level or above fails the gate. */
export const AXE_MIN_SEVERITY = "moderate" as const;

const SEVERITY_RANK: Record<string, number> = {
  minor: 1,
  moderate: 2,
  serious: 3,
  critical: 4,
};
const MIN_RANK = SEVERITY_RANK[AXE_MIN_SEVERITY];

/** Filter axe violations down to those at or above the moderate threshold. */
export function filterModerateOrAbove(
  violations: ReadonlyArray<AxeResult>,
): ReadonlyArray<AxeResult> {
  return violations.filter((v) => {
    if (v.impact == null) return false;
    const rank = SEVERITY_RANK[v.impact];
    return typeof rank === "number" && rank >= MIN_RANK;
  });
}

/**
 * Run axe-core against a DOM node and return only violations at or
 * above the moderate severity threshold. Throws nothing — callers
 * `expect(violations).toEqual([])`.
 */
export async function runAxeOnChapter(
  node: HTMLElement,
): Promise<ReadonlyArray<AxeResult>> {
  const result: AxeResults = await axe.run(node, axeChapterRules);
  return filterModerateOrAbove(result.violations);
}
