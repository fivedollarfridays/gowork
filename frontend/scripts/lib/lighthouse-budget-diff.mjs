/**
 * W4 Driver C Spotlight #3 — lighthouse-budget-diff library (ESM).
 *
 * Pure functions for parsing lhci `manifest.json` (or the per-run JSON
 * Lighthouse emits), comparing two runs, and surfacing category-score
 * deltas. The CLI shim (lighthouse-budget-diff.mjs at scripts/ root)
 * spawns lhci, locates the two latest runs, and pipes them through these
 * helpers. The functions here have NO filesystem dependency so vitest
 * drives them with synthetic inputs.
 *
 * # Why this exists
 *
 * Lighthouse on CI is variance-prone (5 points of jitter per category is
 * normal). When a PR drops Performance from 92 to 85, the question is :
 * "did THIS PR cause it, or is it noise?" Comparing the median of
 * `numberOfRuns: 3` against the prior median across category scores
 * answers the question. >5pt drop = real regression; <=5pt = noise.
 *
 * # Output contract
 *
 * `diffSummaries(prev, curr)` returns:
 *   {
 *     deltas: [{ category, prev, curr, delta, regression }],
 *     anyRegression: bool,
 *     worstRegression: { category, delta } | null,
 *   }
 *
 * @typedef {Object} CategoryScore
 * @property {string} category — e.g. "performance" | "accessibility"
 * @property {number} score    — 0..1 (Lighthouse native scale)
 *
 * @typedef {Object} CategoryDelta
 * @property {string} category
 * @property {number} prev   — 0..100 (humanized)
 * @property {number} curr   — 0..100 (humanized)
 * @property {number} delta  — curr - prev (positive = improvement)
 * @property {boolean} regression — true when delta < -REGRESSION_THRESHOLD_PTS
 */

/**
 * Drop threshold (in 0..100 points) below which a delta is classified
 * as a regression. 5 points covers the typical Lighthouse-CI variance.
 */
export const REGRESSION_THRESHOLD_PTS = 5;

/** Category names we audit. Matches lighthouserc.json `assert` block. */
export const AUDITED_CATEGORIES = [
  "performance",
  "accessibility",
  "best-practices",
  "seo",
];

/**
 * Extract category scores from a Lighthouse run JSON. Accepts both the
 * raw lhci result shape and the manifest-row shape (where each row has a
 * `summary` property keyed by category).
 *
 * @param {object} run
 * @returns {CategoryScore[]}
 */
export function extractCategoryScores(run) {
  if (!run || typeof run !== "object") return [];
  // Manifest-row shape: { summary: { performance: 0.92, ... } }
  if (run.summary && typeof run.summary === "object") {
    return Object.entries(run.summary)
      .filter(([k, v]) => typeof v === "number" && AUDITED_CATEGORIES.includes(k))
      .map(([category, score]) => ({ category, score }));
  }
  // Raw result shape: { categories: { performance: { score: 0.92 } } }
  if (run.categories && typeof run.categories === "object") {
    return Object.entries(run.categories)
      .filter(([k]) => AUDITED_CATEGORIES.includes(k))
      .map(([category, value]) => {
        const v = /** @type {{ score?: number }} */ (value);
        return { category, score: typeof v.score === "number" ? v.score : 0 };
      });
  }
  return [];
}

/** Round a 0..1 score to a 0..100 integer. */
export function humanize(score) {
  if (typeof score !== "number" || !Number.isFinite(score)) return 0;
  return Math.round(score * 100);
}

/**
 * Diff two arrays of CategoryScore. Categories present in only one side
 * are dropped (no spurious "infinite regression" rows).
 *
 * @param {CategoryScore[]} prev
 * @param {CategoryScore[]} curr
 * @returns {{ deltas: CategoryDelta[], anyRegression: boolean, worstRegression: { category: string, delta: number } | null }}
 */
export function diffSummaries(prev, curr) {
  const prevMap = new Map(prev.map((r) => [r.category, r.score]));
  const currMap = new Map(curr.map((r) => [r.category, r.score]));
  const deltas = [];
  for (const cat of AUDITED_CATEGORIES) {
    if (!prevMap.has(cat) || !currMap.has(cat)) continue;
    const prevPts = humanize(prevMap.get(cat));
    const currPts = humanize(currMap.get(cat));
    const delta = currPts - prevPts;
    const regression = delta < -REGRESSION_THRESHOLD_PTS;
    deltas.push({ category: cat, prev: prevPts, curr: currPts, delta, regression });
  }
  const regressions = deltas.filter((d) => d.regression);
  const anyRegression = regressions.length > 0;
  const worstRegression = regressions.length === 0
    ? null
    : regressions.reduce((acc, d) => (d.delta < acc.delta ? d : acc), regressions[0]);
  return { deltas, anyRegression, worstRegression };
}

/** Format a single delta as a single-line report row. */
export function formatDeltaLine(delta) {
  const sign = delta.delta >= 0 ? "+" : "";
  const tag = delta.regression ? " REGRESSION" : "";
  return `${delta.category}: ${delta.prev} → ${delta.curr} (${sign}${delta.delta})${tag}`;
}

/** Format a full diff summary as a human-readable report. */
export function formatDiffReport(summary) {
  const lines = ["Lighthouse score diff", "====================="];
  for (const d of summary.deltas) lines.push(formatDeltaLine(d));
  if (summary.anyRegression && summary.worstRegression) {
    lines.push("");
    lines.push(
      `WORST: ${summary.worstRegression.category} dropped ${Math.abs(summary.worstRegression.delta)} pts`,
    );
  }
  return lines.join("\n");
}
