/**
 * Pure analytic helpers over the jobs-by-zip data.
 *
 * **Spotlight invention (Awakening Condition #1 — 許可).** The brief
 * didn't list a "fair-chance employer density by category" derivation.
 * Building it here in W2 unblocks two future surfaces without re-reading
 * the data:
 *
 *   1. A heatmap layer (W4 follow-up) — color category clusters by
 *      fair-chance share.
 *   2. A press-kit / README stat ("60% of warehouse employers in our
 *      dataset are fair-chance") — generated from this analytic, never
 *      hand-edited.
 *
 * Pure + deterministic — fits the zero-LLM-in-render-path constraint.
 */

import { JOBS_BY_ZIP_EMPLOYERS, type EmployerPoint } from "./layers/jobsByZipData";

export interface FairChanceShare {
  category: EmployerPoint["category"];
  total: number;
  fairChance: number;
  /** 0..1 — fair-chance share within the category. */
  share: number;
}

/**
 * Compute fair-chance share per employer category.
 *
 * Result is sorted by descending share so editorial copy can render
 * "the 3 fairest categories" without re-sorting.
 */
export function fairChanceShareByCategory(
  employers: readonly EmployerPoint[] = JOBS_BY_ZIP_EMPLOYERS,
): FairChanceShare[] {
  const buckets = new Map<EmployerPoint["category"], { total: number; fc: number }>();
  for (const e of employers) {
    const b = buckets.get(e.category) ?? { total: 0, fc: 0 };
    b.total += 1;
    if (e.fairChance) b.fc += 1;
    buckets.set(e.category, b);
  }
  const out: FairChanceShare[] = [];
  for (const [category, b] of buckets) {
    out.push({
      category,
      total: b.total,
      fairChance: b.fc,
      share: b.total === 0 ? 0 : b.fc / b.total,
    });
  }
  out.sort((a, b) => b.share - a.share);
  return out;
}

/**
 * Backs the Ch4d editorial claim "30% of jobs go dark on credit checks."
 * Returns the share of employers in the dataset that require credit
 * checks (creditCheck=true).
 */
export function creditCheckShare(
  employers: readonly EmployerPoint[] = JOBS_BY_ZIP_EMPLOYERS,
): number {
  if (employers.length === 0) return 0;
  const credit = employers.filter((e) => e.creditCheck).length;
  return credit / employers.length;
}
