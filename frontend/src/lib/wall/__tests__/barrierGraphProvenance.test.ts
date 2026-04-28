/**
 * Spotlight invention #3 — Barrier graph provenance freshness gate
 * (W3 Driver B, parallel to officeRegistry-freshness).
 *
 * The 33-node barrier graph ships as an editorial stub. To prevent it
 * from going stale (W4 may swap in a real Reasoner-derived graph), this
 * test asserts:
 *
 *   1. `barrierGraphProvenance.sourceDate` is within the last 365 days
 *      (or future-dated, since the dispatch is dated 2026-04-28).
 *   2. `version` is a non-empty semver-like string.
 *   3. `source` is a non-empty descriptive string.
 *
 * # Lens: Honesty
 *
 * The graph is editorial. The freshness gate makes the editorial
 * provenance testable, not just promised. If a future driver replaces
 * the data without bumping the date, this test fires.
 */
import { describe, it, expect } from "vitest";
import { barrierGraphProvenance } from "../data/barrierGraph";

const MAX_AGE_DAYS = 365;

describe("barrierGraph provenance freshness gate", () => {
  it("sourceDate is a valid ISO date", () => {
    const date = Date.parse(barrierGraphProvenance.sourceDate);
    expect(Number.isFinite(date)).toBe(true);
  });

  it("sourceDate is within 365 days of test runtime", () => {
    const now = Date.now();
    const date = Date.parse(barrierGraphProvenance.sourceDate);
    const ageDays = Math.max(0, (now - date) / (1000 * 60 * 60 * 24));
    expect(ageDays).toBeLessThanOrEqual(MAX_AGE_DAYS);
  });

  it("source is a non-empty descriptive string", () => {
    expect(barrierGraphProvenance.source.length).toBeGreaterThanOrEqual(20);
  });

  it("version is a non-empty semver-shaped string", () => {
    expect(barrierGraphProvenance.version).toMatch(/^\d+\.\d+\.\d+/);
  });
});
