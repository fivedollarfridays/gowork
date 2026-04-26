// Unit tests for bundle-size-parser (T13.87).
import { describe, it, expect } from "vitest";
import {
  parseBuildOutput,
  compareToBaseline,
  formatReport,
} from "../bundle-size-parser.mjs";

describe("parseBuildOutput", () => {
  it("extracts route name + First Load JS in kB from a Next.js build table", () => {
    const stdout = `
   Linting and checking validity of types ...
   Generating static pages (17/17)
Route (app)                                 Size  First Load JS
┌ ○ /                                    4.32 kB         161 kB
├ ○ /appointments                        73.7 kB         210 kB
├ ƒ /admin/qc                              146 B         103 kB
├ ○ /plan                                 152 kB         328 kB
└ ƒ /shared/[token]                      5.47 kB         129 kB
+ First Load JS shared by all             102 kB
`;
    const routes = parseBuildOutput(stdout);
    expect(routes).toEqual({
      "/": 161,
      "/appointments": 210,
      "/admin/qc": 103,
      "/plan": 328,
      "/shared/[token]": 129,
    });
  });

  it("ignores non-route rows (sitemap.xml, robots.txt, _not-found, shared totals)", () => {
    const stdout = `
Route (app)                                 Size  First Load JS
┌ ○ /                                    4.32 kB         161 kB
├ ○ /_not-found                            146 B         103 kB
├ ○ /robots.txt                            146 B         103 kB
├ ○ /sitemap.xml                           146 B         103 kB
└ ○ /privacy                             3.17 kB         121 kB
+ First Load JS shared by all             102 kB
`;
    const routes = parseBuildOutput(stdout);
    expect(Object.keys(routes).sort()).toEqual(["/", "/privacy"]);
  });

  it("handles MB-sized routes by converting to kB", () => {
    const stdout = `
Route (app)                                 Size  First Load JS
└ ○ /huge                                  2 MB         1.5 MB
`;
    const routes = parseBuildOutput(stdout);
    expect(routes["/huge"]).toBeCloseTo(1536, 0);
  });

  it("returns empty object when no route table is present", () => {
    expect(parseBuildOutput("nothing here")).toEqual({});
  });
});

describe("compareToBaseline", () => {
  const baseline = { "/": 100, "/plan": 300 };

  it("returns ok=true when all routes are within threshold", () => {
    const result = compareToBaseline(
      { "/": 105, "/plan": 320 },
      baseline,
      10,
    );
    expect(result.ok).toBe(true);
    expect(result.regressions).toEqual([]);
  });

  it("flags any route that exceeds baseline by more than threshold pct", () => {
    const result = compareToBaseline(
      { "/": 111, "/plan": 320 }, // / is +11%, /plan is +6.7%
      baseline,
      10,
    );
    expect(result.ok).toBe(false);
    expect(result.regressions).toHaveLength(1);
    expect(result.regressions[0].route).toBe("/");
    expect(result.regressions[0].deltaPct).toBeCloseTo(11, 0);
  });

  it("treats exactly 10% as acceptable (boundary, not regression)", () => {
    const result = compareToBaseline({ "/": 110 }, baseline, 10);
    expect(result.ok).toBe(true);
  });

  it("warns about routes missing from current build", () => {
    const result = compareToBaseline({ "/": 100 }, baseline, 10);
    expect(result.missing).toEqual(["/plan"]);
  });

  it("warns about new routes not in baseline (informational, not failing)", () => {
    const result = compareToBaseline(
      { "/": 100, "/plan": 300, "/new-page": 50 },
      baseline,
      10,
    );
    expect(result.ok).toBe(true);
    expect(result.unknown).toEqual(["/new-page"]);
  });

  it("ignores baseline entries with size 0 (placeholder routes)", () => {
    const result = compareToBaseline(
      { "/": 100, "/zero": 50 },
      { "/": 100, "/zero": 0 },
      10,
    );
    expect(result.ok).toBe(true);
  });
});

describe("formatReport", () => {
  it("includes PASS marker and route table on success", () => {
    const out = formatReport(
      { "/": 100 },
      { "/": 100 },
      { ok: true, regressions: [], missing: [], unknown: [] },
      10,
    );
    expect(out).toContain("PASS");
    expect(out).toContain("/");
  });

  it("includes FAIL marker and lists regressions on failure", () => {
    const out = formatReport(
      { "/": 120 },
      { "/": 100 },
      {
        ok: false,
        regressions: [{ route: "/", current: 120, baseline: 100, deltaPct: 20 }],
        missing: [],
        unknown: [],
      },
      10,
    );
    expect(out).toContain("FAIL");
    expect(out).toContain("+20");
    expect(out).toMatch(/\//);
  });
});
