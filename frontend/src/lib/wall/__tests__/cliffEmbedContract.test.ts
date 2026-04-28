/**
 * Cliff-embed contract — Spotlight invention #3 (W3 Driver A).
 *
 * # Why this exists
 *
 * The Wall's Ch6 "The Math" embeds the existing `BenefitsCliffChart`
 * component (`src/components/plan/BenefitsCliffChart.tsx`). It would be
 * tempting to copy/paste the chart into the wall directory and tweak —
 * which guarantees drift, a second implementation that needs a second
 * test suite, and a demo where the /plan version disagrees with the wall
 * version.
 *
 * This audit walks the wall directory and FAILS the build if any file
 * outside `src/components/plan/` declares its own `BenefitsCliffChart`
 * function or class. The wall MUST import the canonical implementation.
 *
 * Spotlight Lens: Honesty + Structural. The honest move is to admit
 * "we already have this; reuse it." The structural move is to make
 * duplication impossible to commit silently.
 */
import { describe, it, expect } from "vitest";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, sep } from "node:path";

const FRONTEND_ROOT = join(__dirname, "..", "..", "..", "..");
const WALL_ROOT = join(FRONTEND_ROOT, "src", "components", "wall");
const WALL_LIB_ROOT = join(FRONTEND_ROOT, "src", "lib", "wall");

const SKIP_DIRS = new Set(["node_modules", ".next", "dist", "build", ".git"]);
const SCAN_EXTS = new Set([".ts", ".tsx", ".js", ".jsx"]);

function* walk(dir: string): Generator<string> {
  let entries: string[];
  try {
    entries = readdirSync(dir);
  } catch {
    return;
  }
  for (const name of entries) {
    if (SKIP_DIRS.has(name)) continue;
    const full = join(dir, name);
    let st;
    try {
      st = statSync(full);
    } catch {
      continue;
    }
    if (st.isDirectory()) {
      yield* walk(full);
      continue;
    }
    const dot = name.lastIndexOf(".");
    if (dot < 0) continue;
    if (!SCAN_EXTS.has(name.slice(dot))) continue;
    yield full;
  }
}

/** Patterns that indicate a redeclaration of BenefitsCliffChart. */
const FORBIDDEN_PATTERNS: RegExp[] = [
  /export\s+function\s+BenefitsCliffChart\b/,
  /export\s+default\s+function\s+BenefitsCliffChart\b/,
  /export\s+const\s+BenefitsCliffChart\b/,
  /class\s+BenefitsCliffChart\b/,
];

function findRedeclarations(rootDirs: string[]): string[] {
  const violations: string[] = [];
  for (const root of rootDirs) {
    let exists = true;
    try {
      statSync(root);
    } catch {
      exists = false;
    }
    if (!exists) continue;
    for (const file of walk(root)) {
      let content: string;
      try {
        content = readFileSync(file, "utf8");
      } catch {
        continue;
      }
      for (const pat of FORBIDDEN_PATTERNS) {
        if (pat.test(content)) {
          violations.push(file);
          break;
        }
      }
    }
  }
  return violations;
}

describe("cliff-embed contract — wall must import, never duplicate", () => {
  it("no file under components/wall redeclares BenefitsCliffChart", () => {
    const found = findRedeclarations([WALL_ROOT]);
    expect(found).toEqual([]);
  });

  it("no file under lib/wall redeclares BenefitsCliffChart", () => {
    const found = findRedeclarations([WALL_LIB_ROOT]);
    expect(found).toEqual([]);
  });

  it("the canonical chart still exists at components/plan", () => {
    const canonical = join(
      FRONTEND_ROOT,
      "src",
      "components",
      "plan",
      "BenefitsCliffChart.tsx",
    );
    const exists = statSync(canonical).isFile();
    expect(exists).toBe(true);
  });

  it("Ch6 (when shipped) imports BenefitsCliffChart from components/plan", () => {
    const ch6Path = join(
      WALL_ROOT,
      "chapters",
      "Chapter06TheMath.tsx",
    );
    let exists = true;
    try {
      statSync(ch6Path);
    } catch {
      exists = false;
    }
    if (!exists) {
      // Pre-Ch6-ship state: skip this assertion. Once Ch6 lands the
      // path becomes mandatory.
      return;
    }
    const content = readFileSync(ch6Path, "utf8");
    // Accept any of: static `from "..."` import, OR next/dynamic
    // `import("...")` lazy boundary, OR a relative variant. Driver D's
    // W3 maximization moved Ch6 to lazy-load the chart via next/dynamic
    // to keep Recharts out of the eager `/` chunk; the contract still
    // holds (Ch6 never duplicates the chart, only consumes the canonical
    // implementation), the resolution path just runs through dynamic().
    const STATIC_IMPORT_RE = /from\s+["'](?:@\/components\/plan\/BenefitsCliffChart|.*\/components\/plan\/BenefitsCliffChart)["']/;
    const DYNAMIC_IMPORT_RE = /import\s*\(\s*["'](?:@\/components\/plan\/BenefitsCliffChart|.*\/components\/plan\/BenefitsCliffChart)["']\s*\)/;
    const importsCanonical =
      STATIC_IMPORT_RE.test(content) || DYNAMIC_IMPORT_RE.test(content);
    const declaresLocal = FORBIDDEN_PATTERNS.some((p) => p.test(content));
    expect(declaresLocal).toBe(false);
    expect(importsCanonical).toBe(true);
  });
});

describe("cliff-embed contract — file-level scan helper exposed for callers", () => {
  it("walks an empty dir without throwing", () => {
    const fakeDir = join(FRONTEND_ROOT, "this-dir-does-not-exist-xyz");
    const found = findRedeclarations([fakeDir]);
    expect(found).toEqual([]);
  });

  it("FRONTEND_ROOT resolves to a real directory (sanity)", () => {
    const st = statSync(FRONTEND_ROOT);
    expect(st.isDirectory()).toBe(true);
    // Sanity: the path separator is OS-correct (joins, not literals).
    expect(FRONTEND_ROOT.includes(sep)).toBe(true);
  });
});
