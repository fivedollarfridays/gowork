/**
 * Brand asset manifest (Spotlight invention).
 *
 * Single registry of every brand asset the wall ships. Distinct from the
 * PWA web manifest (browser-facing) — this is for scripts: asset gallery
 * pages (/dev/tokens, future /dev/assets), audit tools, and the release
 * runbook so deploy day knows what to verify.
 *
 * Keep in sync with `frontend/public/` whenever a new asset lands. The
 * brand-integrity audit script can later iterate this list to verify
 * file presence at build time.
 */

export type AssetKind = "svg" | "raster" | "font" | "audio";

export interface BrandAsset {
  /** Public-relative path (e.g. "/icon.svg"). */
  path: string;
  /** Categorization for grouping in dev surfaces. */
  kind: AssetKind;
  /** Filename for lookup. */
  name: string;
  /** Optional human-readable description. */
  description?: string;
}

export const BRAND_ASSETS: readonly BrandAsset[] = [
  {
    path: "/icon.svg",
    kind: "svg",
    name: "icon.svg",
    description: "Canonical 16-coord brand mark — G + cyan path-line.",
  },
  {
    path: "/favicon-16.png",
    kind: "raster",
    name: "favicon-16.png",
    description: "16px raster, standard favicon.",
  },
  {
    path: "/favicon-32.png",
    kind: "raster",
    name: "favicon-32.png",
    description: "32px raster, standard favicon.",
  },
  {
    path: "/icon-192.png",
    kind: "raster",
    name: "icon-192.png",
    description: "192px PWA icon.",
  },
  {
    path: "/icon-512.png",
    kind: "raster",
    name: "icon-512.png",
    description: "512px PWA icon, splash + maskable.",
  },
  {
    path: "/apple-icon.png",
    kind: "raster",
    name: "apple-icon.png",
    description: "iOS home-screen icon (180px).",
  },
  {
    path: "/og-image.svg",
    kind: "svg",
    name: "og-image.svg",
    description: "Open Graph + Twitter card hero (1200x630).",
  },
  {
    path: "/sounds/footstep.mp3",
    kind: "audio",
    name: "footstep.mp3",
    description: "Title-sequence completion cue.",
  },
  {
    path: "/sounds/paper-rustle.mp3",
    kind: "audio",
    name: "paper-rustle.mp3",
    description: "Page / chapter transition.",
  },
  {
    path: "/sounds/calculator-click.mp3",
    kind: "audio",
    name: "calculator-click.mp3",
    description: "Cliff-zone wage adjustment cue.",
  },
  {
    path: "/sounds/chime.mp3",
    kind: "audio",
    name: "chime.mp3",
    description: "Outcome / celebration cue.",
  },
  {
    path: "/sounds/wind-ambient.mp3",
    kind: "audio",
    name: "wind-ambient.mp3",
    description: "Optional ambient bed (Ch 1 + Ch 10).",
  },
] as const;

const NAME_INDEX = new Map<string, BrandAsset>();
for (const asset of BRAND_ASSETS) NAME_INDEX.set(asset.name, asset);

/** Lookup an asset by filename. Returns undefined if not registered. */
export function getAsset(name: string): BrandAsset | undefined {
  return NAME_INDEX.get(name);
}
