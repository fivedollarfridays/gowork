#!/usr/bin/env node
/**
 * Brand integrity sweep (Wave 5).
 *
 * Stronger gate than audit-legacy-brand.mjs: greps for legacy hex values,
 * variant spellings, and stale brand chrome that would confuse a judge.
 *
 * Patterns:
 *   - "MontGoWork" (stricter than the legacy script — checks raw text)
 *   - "monto-go-work"
 *   - "Mont Go Work"
 *   - Legacy hex: #1c3461 (old navy), #2a9d8f (old teal)
 *
 * Allowlist parallels audit-legacy-brand.mjs.
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
  /monto-go-work/g,
  /Mont Go Work/g,
  /#1c3461/gi,
  /#2a9d8f/gi,
];

const ALLOWLIST = [
  ["src", "lib", "translations"].join(sep),
  ["src", "lib", "i18n"].join(sep),
  ["src", "app", "privacy"].join(sep),
  ["src", "app", "terms"].join(sep),
  ["src", "__tests__", "brand-mark.test.ts"].join(sep),
  ["src", "__tests__", "audit-brand-script.test.ts"].join(sep),
  ["src", "__tests__", "brand-assets.test.ts"].join(sep),
  ["src", "components", "wall", "__tests__"].join(sep),
  ["src", "components", "layout", "__tests__"].join(sep),
  ["src", "app", "__tests__", "layout-w1.test.tsx"].join(sep),
  ["src", "app", "__tests__", "not-found.test.tsx"].join(sep),
  ["src", "lib", "__tests__", "w1-translation-keys.test.ts"].join(sep),
  ["src", "lib", "wall", "storage.ts"].join(sep),
  ["public", "icon.svg"].join(sep),
  ["scripts", "audit-legacy-brand.mjs"].join(sep),
  ["scripts", "audit-brand-integrity.mjs"].join(sep),
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

if (violations.length > 0) {
  console.error("[audit:brand-integrity] Brand-integrity violations:");
  for (const v of violations) {
    console.error(`  ${v.file} :: ${v.pattern} (x${v.count})`);
  }
  process.exit(1);
}

console.log("[audit:brand-integrity] OK — brand chrome clean.");
process.exit(0);
