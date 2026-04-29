/**
 * polish-2 Driver D — T43 focus-ring audit.
 *
 * Every interactive element on the home route must carry a visible focus
 * affordance. Per the polish-2 dispatch the contract is :
 *   - 2px cyan focus ring
 *   - 2px offset
 *   - 200ms entry transition
 *
 * Implementing all of that is Driver A's CSS lane. This test guards the
 * weaker (but enforceable) condition: NO interactive element ships
 * `outline: none` (or equivalent) without an explicit focus-visible
 * disambiguator class (`focus-visible:ring`, `focus-visible:outline`,
 * etc.). The `.skip-to-content` element is exempt — it suppresses the
 * outline because the visible class itself IS the focus affordance
 * (high-contrast cyan pill).
 *
 * Implemented as a static source scan rather than a jsdom Tab-cycle: the
 * full home tree mounts dynamic chapters that race :focus-visible state
 * unreliably under jsdom's keyboard-event model, but a source scan locks
 * the contract everywhere a developer would otherwise sneak `outline:
 * none` past review.
 */
import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..", "..", "..");

const ALLOWED_BARE_OUTLINE_NONE = new Set<string>([
  // The skip-to-content link is a focus-visible-only target with its own
  // visible affordance (the cyan pill); the outline-none is intentional.
  path.resolve(FRONTEND_ROOT, "src/app/styles/tokens/layout.css"),
  // Auto-generated critical.css inherits the allowed outline-none from
  // tokens/layout.css; treat it as a derived artifact.
  path.resolve(FRONTEND_ROOT, "src/app/styles/critical.css"),
]);

function walk(dir: string, exts: string[], out: string[] = []): string[] {
  for (const name of fs.readdirSync(dir)) {
    if (name === "node_modules" || name === ".next" || name === "__tests__")
      continue;
    const p = path.join(dir, name);
    const stat = fs.statSync(p);
    if (stat.isDirectory()) {
      walk(p, exts, out);
    } else if (exts.some((e) => p.endsWith(e))) {
      out.push(p);
    }
  }
  return out;
}

describe("polish-2 T43 — focus-ring audit on the home route", () => {
  it("no home component sets outline:none without a focus-visible disambiguator", () => {
    const homeDir = path.resolve(FRONTEND_ROOT, "src/components/home");
    const wallDir = path.resolve(FRONTEND_ROOT, "src/components/wall");
    const files = [...walk(homeDir, [".tsx"]), ...walk(wallDir, [".tsx"])];
    const violations: string[] = [];

    for (const f of files) {
      const src = fs.readFileSync(f, "utf-8");
      // Look for bare outline-none / outline: none not paired with a
      // focus-visible:ring or focus-visible:outline directive elsewhere
      // in the same file.
      const hasBareOutlineNone =
        /outline-none/.test(src) || /outline:\s*none/.test(src);
      if (!hasBareOutlineNone) continue;
      const hasFocusVisibleRing =
        /focus-visible:ring/.test(src) ||
        /focus-visible:outline/.test(src) ||
        /focus-visible:bg/.test(src);
      if (!hasFocusVisibleRing) violations.push(path.relative(FRONTEND_ROOT, f));
    }

    expect(
      violations,
      `Files set outline:none/outline-none WITHOUT a focus-visible affordance:\n  ${violations.join("\n  ")}`,
    ).toEqual([]);
  });

  it("no home component overrides :focus { outline: none } in inline CSS", () => {
    const stylesDir = path.resolve(FRONTEND_ROOT, "src/app/styles");
    const files = walk(stylesDir, [".css"]);
    const violations: string[] = [];
    for (const f of files) {
      if (ALLOWED_BARE_OUTLINE_NONE.has(f)) continue;
      const src = fs.readFileSync(f, "utf-8");
      // Match `:focus { ... outline: none ... }` (any whitespace).
      if (/:focus[^{]*\{[^}]*outline:\s*none/.test(src)) {
        violations.push(path.relative(FRONTEND_ROOT, f));
      }
    }
    expect(
      violations,
      `Stylesheet(s) suppress :focus outline without an offsetting affordance:\n  ${violations.join("\n  ")}`,
    ).toEqual([]);
  });

  it("the global focus-visible token (cyan ring) is declared in the design system", () => {
    const tokensDir = path.resolve(FRONTEND_ROOT, "src/app/styles/tokens");
    const files = walk(tokensDir, [".css"]);
    const concatenated = files.map((f) => fs.readFileSync(f, "utf-8")).join("\n");
    // Loose contract: somewhere in tokens we declare a cyan focus token,
    // a 2px ring, or use the `--accent-cyan` variable in a focus rule.
    // Driver A owns the precise rule; this only asserts presence of the
    // cyan accent token (which the rules cascade from).
    expect(concatenated).toMatch(/--accent-cyan/);
  });
});
