#!/usr/bin/env node
/**
 * polish-2 T47 — chapter-thumbs responsive variant builder (Driver D).
 *
 * Reads `frontend/public/home/chapter-thumbs/0[1-8]-*.jpg` and emits a
 * 200w / 400w / 800w × {webp, avif} variant set next to each source so
 * Driver A's `ChapterRailTooltip` can ship a `<picture>` with the
 * correct `srcset` + `sizes`.
 *
 * `planChapterThumbs(srcs)` is a pure function (no I/O) that returns
 * the expected output plan; it is unit-tested.
 *
 * The CLI shim attempts to load `sharp` and processes each image. When
 * sharp is not available, it logs the would-be outputs and exits 0
 * without failing the build (so contributors without sharp can still
 * run the smoke test).
 */

import { existsSync, readdirSync, statSync } from "node:fs";
import { dirname, basename, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const FRONTEND_ROOT = resolve(HERE, "..");
const THUMBS_DIR = resolve(FRONTEND_ROOT, "public/home/chapter-thumbs");

const SIZES = [200, 400, 800];
const FORMATS = ["webp", "avif"];

/**
 * Build the I/O plan: (inputs) → list of { src, dest, width, format }.
 * Pure: no fs calls.
 *
 * @param {string[]} srcs absolute paths to source JPGs
 * @returns {Array<{ src: string; dest: string; width: number; format: string }>}
 */
export function planChapterThumbs(srcs) {
  const plan = [];
  for (const src of srcs) {
    const name = basename(src).replace(/\.(jpe?g|png)$/i, "");
    const dir = dirname(src);
    for (const width of SIZES) {
      for (const format of FORMATS) {
        plan.push({
          src,
          dest: join(dir, `${name}-${width}.${format}`),
          width,
          format,
        });
      }
    }
  }
  return plan;
}

/**
 * Discover JPG sources by walking the thumbs dir.
 *
 * @returns {string[]}
 */
function discoverSources() {
  if (!existsSync(THUMBS_DIR)) return [];
  return readdirSync(THUMBS_DIR)
    .filter((n) => /^0[1-8]-.*\.(jpe?g|png)$/i.test(n))
    .map((n) => join(THUMBS_DIR, n))
    .filter((p) => statSync(p).isFile());
}

async function loadSharp() {
  try {
    const mod = await import("sharp");
    return mod.default ?? mod;
  } catch {
    return null;
  }
}

async function processOne(sharp, entry) {
  const pipeline = sharp(entry.src).resize({ width: entry.width });
  const formatted =
    entry.format === "webp"
      ? pipeline.webp({ quality: 80 })
      : pipeline.avif({ quality: 55 });
  await formatted.toFile(entry.dest);
}

async function main() {
  const sharp = await loadSharp();
  const sources = discoverSources();
  const plan = planChapterThumbs(sources);

  if (!sharp) {
    // eslint-disable-next-line no-console
    console.log(
      `[chapter-thumbs] sharp not available — skipping. Would emit ${plan.length} variants:`,
    );
    for (const entry of plan) {
      // eslint-disable-next-line no-console
      console.log(`  ${entry.dest} (${entry.width}w ${entry.format})`);
    }
    return;
  }

  let ok = 0;
  let fail = 0;
  for (const entry of plan) {
    try {
      await processOne(sharp, entry);
      ok++;
    } catch (err) {
      fail++;
      // eslint-disable-next-line no-console
      console.error(`[chapter-thumbs] FAIL ${entry.dest}: ${err}`);
    }
  }
  // eslint-disable-next-line no-console
  console.log(`[chapter-thumbs] ${ok} ok / ${fail} fail (of ${plan.length})`);
}

const invokedDirectly =
  process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invokedDirectly) {
  main().catch((err) => {
    // eslint-disable-next-line no-console
    console.error(err);
    process.exit(1);
  });
}
