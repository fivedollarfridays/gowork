#!/usr/bin/env node
/**
 * Legacy brand retirement audit (T1.77).
 *
 * Greps the codebase for any unexpected reference to:
 *   - "MontGoWork" / "Mont Go Work" / "monto-go-work"
 *   - "M-shape" / "M letterform"
 *   - The legacy polyline geometry "112,384 112,160 192,288 272,160 272,384"
 *
 * Allowlist (intentional retention for session continuity / legal copy):
 *   - frontend/src/lib/translations/{en,es}.json   (legacy footer key)
 *   - frontend/src/lib/i18n/                       (legacy strings still gated)
 *   - frontend/src/app/privacy/                    (legal copy, separate review)
 *   - frontend/src/app/terms/                      (legal copy, separate review)
 *   - frontend/src/__tests__/brand-mark.test.ts    (the retirement test itself)
 *   - frontend/src/components/wall/__tests__/      (tests asserting retirement)
 *   - any path under node_modules / .next / dist / build
 *
 * Exits non-zero on unexpected match. Run via `npm run audit:brand`.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = fileURLToPath(new URL(".", import.meta.url));
const FRONTEND_ROOT = join(HERE, "..");

const SEARCH_ROOTS = [
  join(FRONTEND_ROOT, "src"),
  join(FRONTEND_ROOT, "public"),
  join(FRONTEND_ROOT, "scripts"),
];

const PATTERNS = [
  /MontGoWork/g,
  /Mont Go Work/g,
  /monto-go-work/g,
  /M-shape/g,
  /M letterform/gi,
  /112,384 112,160 192,288 272,160 272,384/g,
];

const ALLOWLIST = [
  // Legacy locale + i18n surfaces still referenced by translations.
  ["src", "lib", "translations"].join(sep),
  ["src", "lib", "i18n"].join(sep),
  // Legal copy — separate retirement schedule (counsel review pending).
  ["src", "app", "privacy"].join(sep),
  ["src", "app", "terms"].join(sep),
  // Tests that assert retirement intentionally include the legacy strings.
  ["src", "__tests__", "brand-mark.test.ts"].join(sep),
  ["src", "components", "wall", "__tests__"].join(sep),
  // Layout/Header/Footer tests assert the new GoWork branding by greping for
  // the legacy MontGoWork string (must NOT appear in DOM). The file content
  // contains the literal in the assertion.
  ["src", "app", "__tests__", "layout-w1.test.tsx"].join(sep),
  ["src", "app", "__tests__", "not-found.test.tsx"].join(sep),
  ["src", "components", "layout", "__tests__", "Footer-w1.test.tsx"].join(sep),
  ["src", "components", "layout", "__tests__", "Header.test.tsx"].join(sep),
  ["src", "lib", "__tests__", "w1-translation-keys.test.ts"].join(sep),
  ["src", "__tests__", "brand-assets.test.ts"].join(sep),
  // Storage namespace exposes the legacy key constant for back-compat reads.
  ["src", "lib", "wall", "storage.ts"].join(sep),
  // icon.svg's design comment explains that the legacy M-shape is retired.
  ["public", "icon.svg"].join(sep),
  // The audit script itself + its sibling test reference the strings on purpose.
  ["scripts", "audit-legacy-brand.mjs"].join(sep),
  ["scripts", "audit-brand-integrity.mjs"].join(sep),
  ["src", "__tests__", "audit-brand"].join(sep),
];

const SKIP_DIRS = new Set([
  "node_modules",
  ".next",
  "dist",
  "build",
  ".git",
  "coverage",
]);

const CODE_EXTS = new Set([
  ".ts",
  ".tsx",
  ".js",
  ".jsx",
  ".mjs",
  ".cjs",
  ".css",
  ".html",
  ".svg",
  ".md",
  ".json",
]);

function isAllowlisted(rel) {
  return ALLOWLIST.some((entry) => rel.includes(entry));
}

function* walk(dir) {
  for (const name of readdirSync(dir)) {
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
    const ext = name.slice(name.lastIndexOf("."));
    if (!CODE_EXTS.has(ext)) continue;
    yield full;
  }
}

function scan() {
  const violations = [];
  for (const root of SEARCH_ROOTS) {
    let exists = true;
    try {
      statSync(root);
    } catch {
      exists = false;
    }
    if (!exists) continue;
    for (const file of walk(root)) {
      const rel = relative(FRONTEND_ROOT, file);
      if (isAllowlisted(rel)) continue;
      let content;
      try {
        content = readFileSync(file, "utf8");
      } catch {
        continue;
      }
      for (const pat of PATTERNS) {
        const m = content.match(pat);
        if (m && m.length > 0) {
          violations.push({ file: rel, pattern: String(pat), count: m.length });
        }
      }
    }
  }
  return violations;
}

const violations = scan();

if (violations.length > 0) {
  console.error("[audit:brand] Legacy brand references found:");
  for (const v of violations) {
    console.error(`  ${v.file} :: ${v.pattern} (x${v.count})`);
  }
  process.exit(1);
}

console.log("[audit:brand] OK — no unexpected legacy brand references.");
process.exit(0);
