/**
 * W5 Driver C — T5.C.6 part 1.
 *
 * Pins the Lighthouse CI configuration so the four submission-gate floors
 * (perf, a11y, best-practices, SEO) cannot silently drift below their
 * agreed minimums. Performance was relaxed 0.9 -> 0.8 on 2026-04-30 after
 * the post-narrative-reset homepage (Mapbox + GSAP + 8 chapters in initial
 * bundle) hit a 0.84-0.95 variance band on shared GitHub Actions runners
 * and was failing CI on commits that had not regressed perf. The other
 * three categories (a11y, best-practices, SEO) stay at 0.9 — those are
 * NOT subject to the same flakiness and remain hard-gated. Restore perf
 * to 0.9 once Mapbox + chapter graph are lazy-loaded post-hackathon.
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

  it("performance floor is at least 0.80 (relaxed 2026-04-30; restore to 0.9 post-hackathon)", () => {
    const a = cfg.ci.assert.assertions["categories:performance"];
    expect(Array.isArray(a)).toBe(true);
    const [severity, opts] = a;
    expect(severity).toBe("error");
    expect(opts.minScore).toBeGreaterThanOrEqual(0.8);
    // Belt-and-braces: also pin the upper bound so a future commit can't
    // silently drop the floor below 0.8 (the agreed editorial baseline).
    expect(opts.minScore).toBeLessThanOrEqual(0.9);
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
