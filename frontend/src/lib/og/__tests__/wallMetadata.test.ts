/**
 * Spotlight invention #7 (W4 Driver D) — wallMetadata.test.ts.
 *
 * `buildWallMetadata({ chapter, locale })` returns a Next.js Metadata
 * object pointing at the right per-chapter OG card. Used by:
 *   - The Wall root page metadata (chapter=undefined → /api/og/default)
 *   - A future per-chapter route (e.g. /chapter/[n]) that wants its own
 *     OG card
 *   - Press-kit static export (W5)
 *
 * Plus `chapterFragmentToOgImage(fragment)` — the URL fragment-to-card
 * resolver for Twitter unfurl hints.
 *
 * Pure function. No fetch. No env reads beyond `NEXT_PUBLIC_SITE_URL`.
 */

import { describe, it, expect } from "vitest";
import {
  buildWallMetadata,
  chapterFragmentToOgImage,
  hreflangFor,
} from "../wallMetadata";

describe("buildWallMetadata — site-level metadata", () => {
  it("default (no chapter) points at /api/og/default", () => {
    const meta = buildWallMetadata();
    const og = meta.openGraph;
    expect(og).toBeDefined();
    const images = og?.images as Array<{ url: string }> | undefined;
    expect(images?.[0]?.url).toContain("/api/og/default");
  });

  it("chapter=7 points at /api/og/7", () => {
    const meta = buildWallMetadata({ chapter: 7 });
    const og = meta.openGraph;
    const images = og?.images as Array<{ url: string }> | undefined;
    expect(images?.[0]?.url).toContain("/api/og/7");
  });

  it("locale=es appends ?locale=es", () => {
    const meta = buildWallMetadata({ chapter: 1, locale: "es" });
    const og = meta.openGraph;
    const images = og?.images as Array<{ url: string }> | undefined;
    expect(images?.[0]?.url).toContain("/api/og/1");
    expect(images?.[0]?.url).toContain("locale=es");
  });

  it("emits a Twitter card image at the same URL", () => {
    const meta = buildWallMetadata({ chapter: 7 });
    const tw = meta.twitter as { images?: string[] | { url: string }[] } | undefined;
    expect(tw).toBeDefined();
    const images = tw?.images;
    expect(images).toBeDefined();
    const first = Array.isArray(images)
      ? typeof images[0] === "string"
        ? images[0]
        : (images[0] as { url: string }).url
      : undefined;
    expect(first).toContain("/api/og/7");
  });

  it("includes a 1200×630 image dimension hint", () => {
    const meta = buildWallMetadata({ chapter: 1 });
    const images = meta.openGraph?.images as Array<{ width?: number; height?: number }>;
    expect(images?.[0]?.width).toBe(1200);
    expect(images?.[0]?.height).toBe(630);
  });
});

describe("chapterFragmentToOgImage — URL fragment routing", () => {
  it("'#chapter-7' → /api/og/7", () => {
    expect(chapterFragmentToOgImage("#chapter-7")).toContain("/api/og/7");
  });

  it("'chapter-3' (no hash) → /api/og/3", () => {
    expect(chapterFragmentToOgImage("chapter-3")).toContain("/api/og/3");
  });

  it("unknown fragment → /api/og/default", () => {
    expect(chapterFragmentToOgImage("#about")).toContain("/api/og/default");
  });

  it("empty fragment → /api/og/default", () => {
    expect(chapterFragmentToOgImage("")).toContain("/api/og/default");
  });

  it("fragment 'chapter-99' (out of range) → /api/og/default", () => {
    expect(chapterFragmentToOgImage("#chapter-99")).toContain("/api/og/default");
  });
});

describe("hreflangFor — locale-aware language hints", () => {
  it("declares en + es alternates", () => {
    const lang = hreflangFor({ chapter: 1 });
    expect(lang.languages).toBeDefined();
    const langs = lang.languages as Record<string, string>;
    expect(Object.keys(langs)).toContain("en");
    expect(Object.keys(langs)).toContain("es");
  });

  it("the en alternate has no `?locale=` query, es does", () => {
    const lang = hreflangFor({ chapter: 1 });
    const langs = lang.languages as Record<string, string>;
    expect(langs.en).not.toMatch(/locale=es/);
    expect(langs.es).toMatch(/locale=es/);
  });
});
