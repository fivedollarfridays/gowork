#!/usr/bin/env node
/**
 * generate-static-og.mjs — W5 Driver B (T5.B.5)
 *
 * Generates static fallback PNGs for every Wall chapter + the default
 * site card, by hitting the local dev server's /api/og/<chapter> route
 * and writing the response body to frontend/public/og/<chapter>.png.
 *
 * # Why static fallbacks
 *
 * The dynamic OG route uses Vercel's @vercel/og (Satori under the hood)
 * to compose 1200×630 PNGs at request time. Satori is fast and edge-
 * native, but it can fail on demo day for reasons outside our control:
 *  - Edge runtime tipping over on a cold deploy
 *  - Font binary missing (Inter or whatever the composer references)
 *  - Memory budget exceeded on a large chapter card
 *
 * The static fallbacks are the rescue gallery. The /api/og/[chapter]
 * route wraps ImageResponse in try/catch; on any exception it 307-
 * redirects to /og/<chapter>.png. Those PNGs ship from public/og/
 * and don't depend on Satori or the Edge runtime — they're plain
 * static assets.
 *
 * # How to run
 *
 * 1. In one terminal, start the dev server:
 *      cd frontend
 *      npm run dev
 * 2. In another terminal, run this script:
 *      cd frontend
 *      node scripts/generate-static-og.mjs
 *
 * The script hits http://localhost:3000/api/og/<chapter> for chapters
 * 1..10 plus /api/og/default, and saves each response to
 * frontend/public/og/<chapter>.png (and .../default.png).
 *
 * # Optional flags
 *
 *   --base-url <url>    override http://localhost:3000
 *   --locale <en|es>    fetch the Spanish-locale variant instead
 *   --out <dir>         override public/og/
 *   --skip-existing     don't re-fetch chapters whose PNGs already exist
 *
 * # Honest uncertainty (C4)
 *
 * Static OG generation requires running the dev server. There's no
 * headless Satori path that works from a worktree (you'd need a node
 * runtime with Edge-API shims). The script + manual run path is the
 * pragmatic version — Shawn runs it post-merge on the deploy box.
 */

import { mkdir, writeFile, access } from "node:fs/promises";
import { constants as fsConstants } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import process from "node:process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const REPO_ROOT = resolve(__dirname, "..");
const DEFAULT_OUT_DIR = join(REPO_ROOT, "public", "og");
const DEFAULT_BASE_URL = "http://localhost:3000";

const CHAPTERS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

function parseArgs(argv) {
  const args = {
    baseUrl: DEFAULT_BASE_URL,
    locale: "en",
    outDir: DEFAULT_OUT_DIR,
    skipExisting: false,
  };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === "--base-url") args.baseUrl = argv[++i];
    else if (a === "--locale") args.locale = argv[++i];
    else if (a === "--out") args.outDir = resolve(argv[++i]);
    else if (a === "--skip-existing") args.skipExisting = true;
    else if (a === "--help" || a === "-h") {
      console.log(
        "Usage: node scripts/generate-static-og.mjs [--base-url URL] " +
          "[--locale en|es] [--out DIR] [--skip-existing]",
      );
      process.exit(0);
    }
  }
  return args;
}

function buildUrl(baseUrl, chapter, locale) {
  const path = chapter === "default" ? "/api/og/default" : `/api/og/${chapter}`;
  const qs = locale === "es" ? "?locale=es" : "";
  return `${baseUrl}${path}${qs}`;
}

async function fileExists(p) {
  try {
    await access(p, fsConstants.F_OK);
    return true;
  } catch {
    return false;
  }
}

async function fetchAndWrite({ url, outPath, label, skipExisting }) {
  if (skipExisting && (await fileExists(outPath))) {
    console.log(`  skip   ${label} — exists at ${outPath}`);
    return { ok: true, skipped: true };
  }
  console.log(`  fetch  ${label} -> ${url}`);
  const res = await fetch(url);
  if (!res.ok) {
    console.error(`  FAIL   ${label} (HTTP ${res.status})`);
    return { ok: false, status: res.status };
  }
  const buf = Buffer.from(await res.arrayBuffer());
  await writeFile(outPath, buf);
  console.log(`  wrote  ${label} (${buf.length} bytes)`);
  return { ok: true, bytes: buf.length };
}

async function main() {
  const args = parseArgs(process.argv);
  console.log(`generate-static-og — base=${args.baseUrl} locale=${args.locale}`);
  console.log(`out dir: ${args.outDir}`);
  await mkdir(args.outDir, { recursive: true });

  const targets = [
    ...CHAPTERS.map((n) => ({
      chapter: n,
      label: `chapter ${n}`,
      filename: `${n}.png`,
    })),
    { chapter: "default", label: "default", filename: "default.png" },
  ];

  const results = [];
  for (const t of targets) {
    const url = buildUrl(args.baseUrl, t.chapter, args.locale);
    const outPath = join(args.outDir, t.filename);
    const r = await fetchAndWrite({
      url,
      outPath,
      label: t.label,
      skipExisting: args.skipExisting,
    });
    results.push({ ...t, ...r });
  }

  const failures = results.filter((r) => !r.ok);
  console.log("");
  console.log(
    `summary: ${results.length - failures.length}/${results.length} OK ` +
      `(${results.filter((r) => r.skipped).length} skipped)`,
  );
  if (failures.length > 0) {
    console.error("Failures:");
    for (const f of failures) {
      console.error(`  - ${f.label}: HTTP ${f.status ?? "?"}`);
    }
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("generate-static-og failed:");
  console.error(err);
  process.exit(1);
});
