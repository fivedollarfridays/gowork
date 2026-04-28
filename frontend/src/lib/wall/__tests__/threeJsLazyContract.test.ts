/**
 * Spotlight invention #2 — Three.js lazy-load contract guard (W3 Driver B).
 *
 * # Why this exists
 *
 * Three.js is a ~150KB dependency. It belongs in the Ch8 lazy chunk only.
 * If a future driver eager-imports `three` or `@react-three/fiber` from
 * a page-level entry point (or from `WallContainer.tsx` directly), the
 * initial `/` bundle balloons and LCP regresses.
 *
 * This test reads the source files of the eager-import candidates and
 * asserts NEGATIVE matches against `three` / `@react-three/fiber` /
 * `@react-three/drei`. The only file that may import them is
 * `BarrierConstellation.tsx`, which is itself only loaded via
 * `next/dynamic({ ssr: false })` from `Chapter08TheGraph.tsx`.
 *
 * Compound Lens — this test guards W3 NOW and W4 NEXT (when life-layers
 * arrive, future drivers MUST keep three.js out of the eager bundle).
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const FRONTEND_ROOT = resolve(__dirname, "..", "..", "..", "..");

/**
 * Files that are part of the EAGER initial bundle for the home page.
 * Three.js / @react-three/* must NOT appear in any of these.
 */
const EAGER_BUNDLE_FILES: readonly string[] = [
  "src/components/wall/WallContainer.tsx",
  "src/components/wall/MapboxScene.tsx",
  "src/components/wall/chapters/Chapter01Continental.tsx",
  "src/components/wall/chapters/Chapter02CityArrival.tsx",
  "src/components/wall/chapters/Chapter03Neighborhood.tsx",
  "src/components/wall/chapters/Chapter04TheWall.tsx",
  "src/components/wall/chapters/Chapter05Labyrinth.tsx",
  "src/components/wall/chapters/Chapter07ThePath.tsx",
  "src/components/wall/chapters/Chapter08TheGraph.tsx",
  "src/components/wall/CarlosAvatar.tsx",
];

const FORBIDDEN_PATTERNS: ReadonlyArray<{ name: string; re: RegExp }> = [
  // Static imports of three / @react-three/*
  { name: "three top-level static import", re: /^\s*import[^;]*from\s+["']three["']/m },
  { name: "@react-three/fiber static import", re: /^\s*import[^;]*from\s+["']@react-three\/fiber["']/m },
  { name: "@react-three/drei static import", re: /^\s*import[^;]*from\s+["']@react-three\/drei["']/m },
  // require() also forbidden
  { name: "require('three')", re: /require\(\s*["']three["']\s*\)/ },
  { name: "require('@react-three/fiber')", re: /require\(\s*["']@react-three\/fiber["']\s*\)/ },
];

describe("Three.js lazy-load contract — eager bundle is three.js-free", () => {
  it.each(EAGER_BUNDLE_FILES)("%s contains no static three.js imports", (rel) => {
    const abs = resolve(FRONTEND_ROOT, rel);
    const src = readFileSync(abs, "utf-8");
    for (const pattern of FORBIDDEN_PATTERNS) {
      expect({ file: rel, pattern: pattern.name, match: pattern.re.test(src) }).toEqual({
        file: rel,
        pattern: pattern.name,
        match: false,
      });
    }
  });
});

describe("Three.js lazy-load contract — Chapter08 uses next/dynamic for the constellation", () => {
  it("Chapter08TheGraph imports BarrierConstellation via next/dynamic", () => {
    const src = readFileSync(
      resolve(
        FRONTEND_ROOT,
        "src/components/wall/chapters/Chapter08TheGraph.tsx",
      ),
      "utf-8",
    );
    expect(src).toMatch(/import\s+dynamic\s+from\s+["']next\/dynamic["']/);
    expect(src).toMatch(
      /dynamic\s*\(\s*\(\s*\)\s*=>\s*import\s*\(\s*["'][^"']*BarrierConstellation["']\s*\)/,
    );
    expect(src).toMatch(/ssr:\s*false/);
  });
});

describe("Three.js lazy-load contract — BarrierConstellation is the ONLY file allowed to import three.js", () => {
  it("BarrierConstellation.tsx imports @react-three/fiber (lazy chunk)", () => {
    const src = readFileSync(
      resolve(FRONTEND_ROOT, "src/components/wall/BarrierConstellation.tsx"),
      "utf-8",
    );
    expect(src).toMatch(/from\s+["']@react-three\/fiber["']/);
  });
});
