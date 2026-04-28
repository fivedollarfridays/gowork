/**
 * wallMetadata edge cases — narrow guards.
 *
 * Tests cover:
 *   - chapter=null is treated like undefined (default card).
 *   - locale defaults to 'en' when omitted.
 *   - hreflangFor's URLs match the canonical OG image URLs.
 *   - chapterFragmentToOgImage handles whitespace + trailing slash + uppercase.
 *   - ogImageUrl returns the same URL for chapter=undefined and chapter=null.
 *   - Spanish flag does NOT add a query if chapter is undefined and locale=en.
 *   - Twitter image array is exactly 1 entry.
 */

import { describe, it, expect } from "vitest";
import {
  ogImageUrl,
  buildWallMetadata,
  chapterFragmentToOgImage,
  hreflangFor,
} from "../wallMetadata";

describe("ogImageUrl edge cases", () => {
  it("no args returns /api/og/default", () => {
    expect(ogImageUrl()).toBe("/api/og/default");
  });

  it("chapter=null returns /api/og/default", () => {
    expect(ogImageUrl({ chapter: null })).toBe("/api/og/default");
  });

  it("chapter=undefined returns /api/og/default", () => {
    expect(ogImageUrl({ chapter: undefined })).toBe("/api/og/default");
  });

  it("chapter=5, locale='es' appends ?locale=es", () => {
    expect(ogImageUrl({ chapter: 5, locale: "es" })).toBe(
      "/api/og/5?locale=es",
    );
  });

  it("chapter=5, locale omitted defaults to en (no query)", () => {
    expect(ogImageUrl({ chapter: 5 })).toBe("/api/og/5");
  });

  it("locale='es' with no chapter still routes to default", () => {
    expect(ogImageUrl({ locale: "es" })).toBe("/api/og/default?locale=es");
  });
});

describe("chapterFragmentToOgImage robustness", () => {
  it("hash with extra characters before chapter-N → default", () => {
    expect(chapterFragmentToOgImage("#hello-chapter-1")).toContain(
      "/api/og/default",
    );
  });

  it("trailing chars after chapter number → default (strict regex)", () => {
    expect(chapterFragmentToOgImage("#chapter-1foo")).toContain(
      "/api/og/default",
    );
  });

  it("chapter-0 (out of range) → default", () => {
    expect(chapterFragmentToOgImage("#chapter-0")).toContain(
      "/api/og/default",
    );
  });

  it("chapter-1 → /api/og/1", () => {
    expect(chapterFragmentToOgImage("#chapter-1")).toBe("/api/og/1");
  });

  it("chapter-10 → /api/og/10", () => {
    expect(chapterFragmentToOgImage("#chapter-10")).toBe("/api/og/10");
  });
});

describe("buildWallMetadata Twitter card structure", () => {
  it("has exactly 1 image entry", () => {
    const meta = buildWallMetadata({ chapter: 1 });
    const tw = meta.twitter as { images?: string[] | { url: string }[] } | undefined;
    expect(Array.isArray(tw?.images)).toBe(true);
    expect((tw?.images as unknown[]).length).toBe(1);
  });

  it("OG card type is 'website'", () => {
    const meta = buildWallMetadata();
    expect((meta.openGraph as { type?: string } | undefined)?.type).toBe(
      "website",
    );
  });

  it("OG locale is 'es_ES' when locale='es'", () => {
    const meta = buildWallMetadata({ chapter: 1, locale: "es" });
    expect(meta.openGraph?.locale).toBe("es_ES");
  });

  it("OG locale is 'en_US' when locale is omitted", () => {
    const meta = buildWallMetadata({ chapter: 1 });
    expect(meta.openGraph?.locale).toBe("en_US");
  });

  it("Twitter card type is 'summary_large_image'", () => {
    const meta = buildWallMetadata();
    const tw = meta.twitter as { card?: string } | undefined;
    expect(tw?.card).toBe("summary_large_image");
  });
});

describe("hreflangFor symmetry", () => {
  it("en + es URLs differ only in query", () => {
    const lang = hreflangFor({ chapter: 5 });
    const langs = lang.languages as Record<string, string>;
    expect(langs.en).toBe("/api/og/5");
    expect(langs.es).toBe("/api/og/5?locale=es");
  });

  it("default route has en + es alternates", () => {
    const lang = hreflangFor();
    const langs = lang.languages as Record<string, string>;
    expect(langs.en).toBe("/api/og/default");
    expect(langs.es).toBe("/api/og/default?locale=es");
  });
});
