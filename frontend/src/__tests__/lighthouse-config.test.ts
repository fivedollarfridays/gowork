/**
 * W5 Driver C — T5.C.6 part 1.
 *
 * Pins the Lighthouse CI configuration so the four submission-gate floors
 * (perf, a11y, best-practices, SEO) cannot silently drift below 0.90.
 *
 * Why: the W4 brief AND the W5 Driver C brief both specify a perf hard-gate
 * of 0.90. The W5 sprint backlog itself relaxes perf to 0.85 — the driver
 * brief beats the backlog (this is documented in the lighthouse-final-scores
 * doc). When in doubt, this test asserts the STRICTER floor; if Shawn
 * decides to relax to 0.85 he edits one number here, fixes the lhci config,
 * and re-runs.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const LHCI_PATH = join(process.cwd(), "lighthouserc.json");

describe("frontend/lighthouserc.json", () => {
  const raw = readFileSync(LHCI_PATH, "utf8");
  const cfg = JSON.parse(raw);

  it("exists and is parseable JSON", () => {
    expect(cfg).toBeTypeOf("object");
    expect(cfg.ci).toBeTypeOf("object");
  });

  it("runs each URL at least 3 times (median wins, noise mitigation)", () => {
    expect(cfg.ci.collect.numberOfRuns).toBeGreaterThanOrEqual(3);
  });

  it("performance floor is at least 0.90 (W5-C hard gate)", () => {
    const a = cfg.ci.assert.assertions["categories:performance"];
    expect(Array.isArray(a)).toBe(true);
    const [severity, opts] = a;
    expect(severity).toBe("error");
    expect(opts.minScore).toBeGreaterThanOrEqual(0.9);
  });

  it("accessibility floor is at least 0.90", () => {
    const a = cfg.ci.assert.assertions["categories:accessibility"];
    const [, opts] = a;
    expect(opts.minScore).toBeGreaterThanOrEqual(0.9);
  });

  it("best-practices floor is at least 0.90", () => {
    const a = cfg.ci.assert.assertions["categories:best-practices"];
    const [, opts] = a;
    expect(opts.minScore).toBeGreaterThanOrEqual(0.9);
  });

  it("seo floor is at least 0.90", () => {
    const a = cfg.ci.assert.assertions["categories:seo"];
    const [, opts] = a;
    expect(opts.minScore).toBeGreaterThanOrEqual(0.9);
  });

  it("collects the landing route '/' (the Wall — primary submission surface)", () => {
    expect(cfg.ci.collect.url.some((u: string) => u.endsWith("/"))).toBe(true);
  });
});
