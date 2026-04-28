/**
 * W3 Driver D Spotlight invention — Bundle budget contract guard for the
 * Recharts lazy boundary.
 *
 * # Why this exists
 *
 * Driver A's Chapter06TheMath embeds the BenefitsCliffChart from
 * components/plan. That chart pulls in `recharts` (~130KB minified) plus
 * `react-smooth` (animation easings). If a future driver flips back to a
 * static `import { BenefitsCliffChart }` from a Wall chapter, the eager
 * `/` chunk swells back to ~273KB First Load JS — re-introducing the
 * regression Driver D fixed.
 *
 * This test pins a static contract: every chapter source MUST NOT
 * statically import recharts OR import BenefitsCliffChart directly. The
 * only legal path is `next/dynamic({ ssr: false })` (or no usage at all).
 *
 * # Compound Lens
 *
 * - W3 today: keep `/` First Load JS < 200KB.
 * - W4 next: when life-layers add their own chart embeds, the same guard
 *   forces them through the lazy boundary too.
 * - W5 submission: the bundle size becomes a judging metric; this test
 *   makes regression loud, not silent.
 */
import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { resolve, join } from "node:path";

const FRONTEND_ROOT = resolve(__dirname, "..", "..", "..", "..");
const CHAPTERS_DIR = resolve(FRONTEND_ROOT, "src/components/wall/chapters");
const WALL_DIR = resolve(FRONTEND_ROOT, "src/components/wall");

const STATIC_RECHARTS_RE = /^\s*import[^;]*from\s+["']recharts["']/m;
const STATIC_REACT_SMOOTH_RE = /^\s*import[^;]*from\s+["']react-smooth["']/m;
const STATIC_CLIFF_CHART_RE =
  /^\s*import[^;]*\{\s*BenefitsCliffChart\s*\}[^;]*from\s+["']@\/components\/plan\/BenefitsCliffChart["']/m;
const REQUIRE_RECHARTS_RE = /require\(\s*["']recharts["']\s*\)/;

function listTsxRecursive(dir: string): readonly string[] {
  if (!existsSync(dir)) return [];
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const s = statSync(full);
    if (s.isDirectory()) {
      // Tests live under __tests__ — they're allowed to inspect anything.
      if (entry === "__tests__") continue;
      out.push(...listTsxRecursive(full));
      continue;
    }
    if (entry.endsWith(".tsx") || entry.endsWith(".ts")) out.push(full);
  }
  return out;
}

describe("Bundle budget — chapters/* MUST NOT statically import recharts", () => {
  const chapterFiles = listTsxRecursive(CHAPTERS_DIR);

  it("at least one chapter file is present (sanity)", () => {
    expect(chapterFiles.length).toBeGreaterThan(0);
  });

  it.each(chapterFiles)("%s — no static recharts import", (file) => {
    const src = readFileSync(file, "utf-8");
    expect(STATIC_RECHARTS_RE.test(src)).toBe(false);
    expect(STATIC_REACT_SMOOTH_RE.test(src)).toBe(false);
    expect(REQUIRE_RECHARTS_RE.test(src)).toBe(false);
  });

  it.each(chapterFiles)(
    "%s — no static `import { BenefitsCliffChart }` (must be next/dynamic)",
    (file) => {
      const src = readFileSync(file, "utf-8");
      expect(STATIC_CLIFF_CHART_RE.test(src)).toBe(false);
    },
  );
});

describe("Bundle budget — Chapter06 uses next/dynamic for BenefitsCliffChart", () => {
  it("Chapter06TheMath imports BenefitsCliffChart via next/dynamic", () => {
    const ch6 = resolve(CHAPTERS_DIR, "Chapter06TheMath.tsx");
    const src = readFileSync(ch6, "utf-8");
    // Must import next/dynamic
    expect(src).toMatch(/import\s+dynamic\s+from\s+["']next\/dynamic["']/);
    // Must dynamic-import BenefitsCliffChart
    expect(src).toMatch(
      /dynamic\s*\(\s*\(\s*\)\s*=>\s*import\s*\(\s*["'][^"']*BenefitsCliffChart["']/,
    );
    // Must specify ssr: false so Recharts stays in a client-only chunk
    expect(src).toMatch(/ssr:\s*false/);
  });

  it("Chapter06TheMath provides a loading skeleton", () => {
    const ch6 = resolve(CHAPTERS_DIR, "Chapter06TheMath.tsx");
    const src = readFileSync(ch6, "utf-8");
    // Loading component prevents layout shift while the lazy chart hydrates.
    expect(src).toMatch(/loading:\s*\(\s*\)\s*=>\s*<CliffChartSkeleton/);
  });
});

describe("Bundle budget — components/wall/* siblings stay recharts-free", () => {
  // WallContainer + chapter-adjacent components must not pull recharts
  // either, since they all live in the eager initial chunk.
  const eagerWallFiles = readdirSync(WALL_DIR)
    .filter((n) => n.endsWith(".tsx"))
    .map((n) => join(WALL_DIR, n));

  it.each(eagerWallFiles)("%s — no static recharts import", (file) => {
    const src = readFileSync(file, "utf-8");
    expect(STATIC_RECHARTS_RE.test(src)).toBe(false);
    expect(STATIC_REACT_SMOOTH_RE.test(src)).toBe(false);
  });
});
