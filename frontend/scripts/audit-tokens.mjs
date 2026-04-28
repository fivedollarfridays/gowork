#!/usr/bin/env node
/**
 * Token usage audit (Wave 5).
 *
 * Parses every CSS partial under src/app/styles/tokens/* to extract custom
 * properties (`--token-name`), then greps the codebase for `var(--token-name)`
 * and matching TS exports. Reports:
 *   - tokens declared but unused
 *   - duplicate declarations across partials
 *   - tokens consumed without a declaration (silent miss)
 *
 * Runs as `npm run audit:tokens`. Non-zero exit on hard violations
 * (consumed-without-declaration). Unused/duplicates print as warnings.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = fileURLToPath(new URL(".", import.meta.url));
const FRONTEND_ROOT = join(HERE, "..");
const TOKENS_DIR = join(FRONTEND_ROOT, "src", "app", "styles", "tokens");
const SEARCH_ROOT = join(FRONTEND_ROOT, "src");

const SKIP_DIRS = new Set([
  "node_modules",
  ".next",
  "dist",
  "build",
  ".git",
  "coverage",
  "__tests__",
]);

const CODE_EXTS = new Set([".ts", ".tsx", ".js", ".jsx", ".mjs", ".css"]);

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

// 1. Extract --token-name declarations from token partials.
const declarations = new Map(); // name -> Set<file>
for (const file of walk(TOKENS_DIR)) {
  const content = readFileSync(file, "utf8");
  const matches = content.matchAll(/(--[a-z][a-z0-9-]+)\s*:/gi);
  for (const m of matches) {
    const name = m[1];
    if (!declarations.has(name)) declarations.set(name, new Set());
    declarations.get(name).add(relative(FRONTEND_ROOT, file));
  }
}

// External vars we declare via JS / consume from third-party libraries.
// These are NOT declared in our token partials but ARE legitimate var()
// targets, so suppress the "undeclared" hard violation.
const EXTERNAL_VARS = new Set([
  // Radix UI dynamic measurements.
  "--radix-select-trigger-height",
  "--radix-select-trigger-width",
  "--radix-select-content-available-height",
  "--radix-popover-trigger-width",
  "--radix-popper-anchor-width",
  // CursorFlashlight sets these inline via JS.
  "--flashlight-x",
  "--flashlight-y",
  // next/font injects these.
  "--font-inter",
]);

// 2. Scan the rest of the codebase for var(--name) usages.
const usages = new Map(); // name -> count
for (const file of walk(SEARCH_ROOT)) {
  const rel = relative(FRONTEND_ROOT, file);
  // Skip the token partials themselves.
  if (rel.startsWith(["src", "app", "styles", "tokens"].join(sep))) continue;
  const content = readFileSync(file, "utf8");
  const matches = content.matchAll(/var\((--[a-z][a-z0-9-]+)/gi);
  for (const m of matches) {
    const name = m[1];
    usages.set(name, (usages.get(name) ?? 0) + 1);
  }
}

// Reporting.
const declaredNames = [...declarations.keys()].sort();
const usedNames = new Set(usages.keys());

const unused = declaredNames.filter((n) => !usedNames.has(n));
const duplicates = declaredNames.filter(
  (n) => declarations.get(n).size > 1,
);
const undeclared = [...usedNames].filter(
  (n) => !declarations.has(n) && !EXTERNAL_VARS.has(n),
);

let exitCode = 0;
if (undeclared.length > 0) {
  console.error("[audit:tokens] HARD: var() usages without declaration:");
  for (const n of undeclared) console.error(`  ${n}`);
  exitCode = 1;
}
if (unused.length > 0) {
  console.warn(`[audit:tokens] ${unused.length} declared but unused:`);
  for (const n of unused) console.warn(`  ${n}`);
}
if (duplicates.length > 0) {
  console.warn(`[audit:tokens] ${duplicates.length} duplicate declarations:`);
  for (const n of duplicates) {
    console.warn(`  ${n} :: ${[...declarations.get(n)].join(", ")}`);
  }
}
if (exitCode === 0) {
  console.log(
    `[audit:tokens] OK — ${declaredNames.length} tokens declared, ${usedNames.size} consumed.`,
  );
}
process.exit(exitCode);
