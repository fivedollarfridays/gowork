#!/usr/bin/env node
/**
 * Render brand SVG thumbnails to PNG via headless Chromium.
 *
 * Why: most social platforms (Instagram upload, Twitter card upload,
 * LinkedIn poster, Slack image upload) accept JPG/PNG only. Our brand
 * thumbnails ship as SVG (resolution-independent, gradient-perfect,
 * ~2KB each), but post-side we need rasters too.
 *
 * Uses Playwright's bundled Chromium (already a dev dep for E2E
 * tests) to render each SVG at its natural viewBox size and snapshot
 * a PNG. Pixel-perfect — Chromium honors the gradient + radial
 * atmosphere washes the same way the production browser does.
 *
 * Usage:
 *   node scripts/render-brand-pngs.mjs
 *
 * Output is written next to the source SVG with the matching basename:
 *   public/brand/gowork-thumbnail-square.svg -> -square.png
 *   public/brand/gowork-thumbnail-wide.svg   -> -wide.png
 *   public/brand/gowork-thumbnail-transparent.svg -> -transparent.png
 *
 * Idempotent: re-running overwrites existing PNGs with the latest SVG
 * geometry. Commit the PNGs alongside the SVGs so consumers don't need
 * Playwright installed.
 */
import { readFileSync, readdirSync, writeFileSync } from "node:fs";
import { resolve, dirname, basename } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const __dirname = dirname(fileURLToPath(import.meta.url));
const BRAND_DIR = resolve(__dirname, "..", "public", "brand");

/** Read viewBox dimensions from the SVG's first <svg> tag. */
function readViewBox(svgPath) {
  const text = readFileSync(svgPath, "utf-8");
  const match = text.match(/viewBox=["']([\d.\s-]+)["']/);
  if (!match) throw new Error(`No viewBox in ${svgPath}`);
  const [minX, minY, w, h] = match[1].trim().split(/\s+/).map(Number);
  if (!Number.isFinite(w) || !Number.isFinite(h)) {
    throw new Error(`Bad viewBox dims in ${svgPath}: ${match[1]}`);
  }
  return { width: w, height: h, minX, minY };
}

/** Wrap the SVG in a minimal HTML doc with the right body sizing. */
function wrapHtml(svgText, width, height, transparent) {
  return `<!doctype html>
<html><head><style>
  html,body{margin:0;padding:0;width:${width}px;height:${height}px;
    background:${transparent ? "transparent" : "transparent"};}
  svg{display:block;width:${width}px;height:${height}px;}
</style></head><body>${svgText}</body></html>`;
}

async function renderOne(browser, svgPath) {
  const { width, height } = readViewBox(svgPath);
  const isTransparent = basename(svgPath).includes("transparent");
  const svgText = readFileSync(svgPath, "utf-8");
  const html = wrapHtml(svgText, width, height, isTransparent);

  const page = await browser.newPage({
    viewport: { width, height },
    deviceScaleFactor: 1,
  });
  await page.setContent(html, { waitUntil: "load" });

  // Give @font-face a beat — Inter is loaded from Google Fonts at
  // runtime in the live site. For these screenshots we accept the
  // system fallback so the render is offline-safe; Chromium will
  // resolve "Inter, system-ui, ..." down to the OS humanist sans
  // (Segoe UI on Windows, Helvetica/Inter on Mac, DejaVu on Linux),
  // which is visually identical for these wordmarks at this size.

  const pngPath = svgPath.replace(/\.svg$/i, ".png");
  await page.screenshot({
    path: pngPath,
    type: "png",
    omitBackground: isTransparent,
    clip: { x: 0, y: 0, width, height },
  });
  await page.close();

  return { svgPath, pngPath, width, height };
}

async function main() {
  const svgs = readdirSync(BRAND_DIR)
    .filter((f) => f.toLowerCase().endsWith(".svg"))
    .map((f) => resolve(BRAND_DIR, f));

  if (svgs.length === 0) {
    console.error(`No SVGs found in ${BRAND_DIR}`);
    process.exit(1);
  }

  console.log(`[render-brand-pngs] Rendering ${svgs.length} SVG(s) via headless Chromium…`);
  const browser = await chromium.launch();
  try {
    for (const svgPath of svgs) {
      const result = await renderOne(browser, svgPath);
      console.log(
        `[render-brand-pngs]   ${basename(result.svgPath)} -> ${basename(result.pngPath)} (${result.width}x${result.height})`,
      );
    }
  } finally {
    await browser.close();
  }
  console.log("[render-brand-pngs] Done.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
