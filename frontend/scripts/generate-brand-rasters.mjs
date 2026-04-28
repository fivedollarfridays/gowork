#!/usr/bin/env node
/**
 * generate-brand-rasters.mjs — W1 Driver C
 *
 * Renders raster outputs from `public/icon.svg` (the GoWork G+path mark)
 * at every required density. Idempotent — safe to re-run.
 *
 * Outputs:
 *   public/favicon-16.png        (16x16)
 *   public/favicon-32.png        (32x32)
 *   public/icon-192.png          (192x192)
 *   public/icon-512.png          (512x512)
 *   public/icon-512-maskable.png (512x512 with safe-zone padding)
 *   public/apple-icon.png        (180x180)
 *
 * Run: `node scripts/generate-brand-rasters.mjs`
 *
 * Sharp is a devDependency installed via `npm install --no-save sharp`
 * during W1 — Driver A owns package.json. If sharp is missing, the script
 * exits with a friendly message and instructions, NOT a crash.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const PUBLIC = join(ROOT, "public");

let sharp;
try {
  sharp = (await import("sharp")).default;
} catch {
  console.error(
    "sharp is not installed. Run `npm install --no-save sharp` first.",
  );
  process.exit(2);
}

// Strict XML parsers (e.g. librsvg/sharp) reject "--" inside comments. Our
// authored icon.svg has rich documentation that uses em-dashes; strip those
// comments only for the rasterizer pipeline. The on-disk file is preserved.
const SOURCE_SVG = readFileSync(join(PUBLIC, "icon.svg"), "utf8").replace(
  /<!--[\s\S]*?-->/g,
  "",
);

// Maskable wrapper: 80% safe zone in the centre, --bg-base behind.
const MASKABLE_SVG = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" role="img" aria-label="GoWork (maskable)">
  <rect width="16" height="16" fill="#0A0E1A"/>
  <g transform="translate(1.6 1.6) scale(0.8)">
    ${SOURCE_SVG.replace(/<\?xml[^>]*\?>/, "").replace(/<!--[\s\S]*?-->/g, "").replace(/<svg[^>]*>/, "").replace(/<\/svg>/, "")}
  </g>
</svg>`;

const TARGETS = [
  { name: "favicon-16.png", size: 16, source: SOURCE_SVG },
  { name: "favicon-32.png", size: 32, source: SOURCE_SVG },
  { name: "apple-icon.png", size: 180, source: SOURCE_SVG },
  { name: "icon-192.png", size: 192, source: SOURCE_SVG },
  { name: "icon-512.png", size: 512, source: SOURCE_SVG },
  { name: "icon-512-maskable.png", size: 512, source: MASKABLE_SVG },
];

let failures = 0;
for (const target of TARGETS) {
  const outPath = join(PUBLIC, target.name);
  try {
    const buffer = await sharp(Buffer.from(target.source))
      .resize(target.size, target.size)
      .png()
      .toBuffer();
    writeFileSync(outPath, buffer);
    console.log(`  wrote ${target.name} (${target.size}x${target.size}, ${buffer.length} bytes)`);
  } catch (err) {
    console.error(`  FAILED ${target.name}: ${err.message ?? err}`);
    failures++;
  }
}

if (failures > 0) {
  console.error(`generate-brand-rasters: ${failures} failure(s).`);
  process.exit(1);
}

console.log("generate-brand-rasters: all targets written.");
