/**
 * T13.116 — Favicon + PWA Manifest + OG/Twitter Meta
 *
 * Verifies that the Next.js Metadata API exports on the root layout and on
 * each top-level route segment carry the full meta suite required for a
 * shareable hackathon submission: title/description, openGraph, twitter,
 * icons (multi-size), and manifest reference. Also asserts the
 * `shared/[token]` route's `generateMetadata` returns valid metadata WITHOUT
 * leaking PII from the share-target payload.
 */
import { describe, it, expect, vi } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

// next/font/google is a build-time helper; in vitest we stub it so the
// root layout module can be imported for its `metadata` export alone.
vi.mock("next/font/google", () => ({
  Inter: () => ({ variable: "--font-inter", className: "font-inter" }),
}));

const { metadata: rootMetadata, viewport: rootViewport } = await import(
  "../layout"
);
const { metadata: dailyMetadata } = await import("../daily/layout");
const { generateMetadata: generateSharedMetadata } = await import(
  "../shared/[token]/layout"
);

const PUBLIC_DIR = resolve(__dirname, "..", "..", "..", "public");

function readManifest(): Record<string, unknown> {
  const raw = readFileSync(resolve(PUBLIC_DIR, "manifest.json"), "utf8");
  return JSON.parse(raw) as Record<string, unknown>;
}

describe("Root layout metadata", () => {
  it("declares title with template + default", () => {
    expect(rootMetadata.title).toBeDefined();
    const title = rootMetadata.title as { default: string; template: string };
    expect(title.default).toBe("MontGoWork");
    expect(title.template).toContain("MontGoWork");
  });

  it("declares description", () => {
    expect(typeof rootMetadata.description).toBe("string");
    expect((rootMetadata.description as string).length).toBeGreaterThan(0);
  });

  it("declares manifest reference", () => {
    expect(rootMetadata.manifest).toBe("/manifest.json");
  });

  it("declares multi-size icons (16, 32, apple-touch 180)", () => {
    const icons = rootMetadata.icons as {
      icon?: Array<{ url: string; sizes?: string }>;
      apple?: Array<{ url: string; sizes?: string }> | string;
    };
    expect(icons).toBeDefined();
    expect(Array.isArray(icons.icon)).toBe(true);
    const sizes = (icons.icon ?? []).map((i) => i.sizes ?? "");
    expect(sizes).toContain("16x16");
    expect(sizes).toContain("32x32");
    // apple-touch-icon is 180x180
    const apple = Array.isArray(icons.apple)
      ? icons.apple.map((i) => i.sizes ?? "")
      : [icons.apple ?? ""];
    expect(apple.join(" ")).toContain("180");
  });

  it("declares openGraph with image, title, description, type=website", () => {
    const og = rootMetadata.openGraph as {
      type?: string;
      title?: string;
      description?: string;
      images?: unknown;
      siteName?: string;
    };
    expect(og).toBeDefined();
    expect(og.type).toBe("website");
    expect(og.siteName).toBe("MontGoWork");
    expect(og.title).toBeTruthy();
    expect(og.description).toBeTruthy();
    expect(og.images).toBeDefined();
    const images = og.images as Array<unknown> | string;
    const arr = Array.isArray(images) ? images : [images];
    expect(arr.length).toBeGreaterThan(0);
  });

  it("exports a viewport.themeColor for browser chrome", () => {
    expect(rootViewport).toBeDefined();
    expect(typeof rootViewport.themeColor).toBe("string");
    expect(rootViewport.themeColor as string).toMatch(/^#[0-9a-fA-F]{6}$/);
  });

  it("declares twitter card with summary_large_image + image", () => {
    const tw = rootMetadata.twitter as {
      card?: string;
      title?: string;
      description?: string;
      images?: unknown;
    };
    expect(tw).toBeDefined();
    expect(tw.card).toBe("summary_large_image");
    expect(tw.title).toBeTruthy();
    expect(tw.description).toBeTruthy();
    expect(tw.images).toBeDefined();
  });
});

describe("Daily route metadata", () => {
  it("declares its own title (overrides root default)", () => {
    expect(dailyMetadata.title).toBeTruthy();
  });

  it("declares description, openGraph and twitter", () => {
    expect(dailyMetadata.description).toBeTruthy();
    const og = dailyMetadata.openGraph as { images?: unknown; title?: string };
    expect(og).toBeDefined();
    expect(og.images).toBeDefined();
    const tw = dailyMetadata.twitter as { card?: string; images?: unknown };
    expect(tw).toBeDefined();
    expect(tw.card).toBe("summary_large_image");
    expect(tw.images).toBeDefined();
  });
});

describe("Shared outcome route metadata", () => {
  it("generateMetadata returns metadata for an arbitrary token", async () => {
    const meta = await generateSharedMetadata({
      params: Promise.resolve({ token: "fixture-token-abc" }),
    });
    expect(meta.title).toBeTruthy();
    expect(meta.description).toBeTruthy();
    const og = meta.openGraph as { images?: unknown; title?: string };
    expect(og).toBeDefined();
    expect(og.images).toBeDefined();
    const tw = meta.twitter as { card?: string; images?: unknown };
    expect(tw).toBeDefined();
    expect(tw.card).toBe("summary_large_image");
    expect(tw.images).toBeDefined();
  });

  it("does NOT leak the raw share token in description / og:title / og:description", async () => {
    const token = "secret-token-xyz-987";
    const meta = await generateSharedMetadata({
      params: Promise.resolve({ token }),
    });
    const desc = (meta.description as string) ?? "";
    const og = meta.openGraph as { title?: string; description?: string };
    const tw = meta.twitter as { title?: string; description?: string };
    expect(desc.includes(token)).toBe(false);
    expect((og.title ?? "").includes(token)).toBe(false);
    expect((og.description ?? "").includes(token)).toBe(false);
    expect((tw.title ?? "").includes(token)).toBe(false);
    expect((tw.description ?? "").includes(token)).toBe(false);
  });

  it("blocks indexing on shared pages (robots noindex)", async () => {
    const meta = await generateSharedMetadata({
      params: Promise.resolve({ token: "any" }),
    });
    const robots = meta.robots as { index?: boolean } | string | undefined;
    if (typeof robots === "object" && robots !== null) {
      expect(robots.index).toBe(false);
    } else {
      expect(typeof robots === "string" ? robots : "").toContain("noindex");
    }
  });
});

describe("PWA manifest.json", () => {
  it("is a valid JSON file in public/", () => {
    const m = readManifest();
    expect(m).toBeTypeOf("object");
  });

  it("declares name, short_name, description, start_url, display", () => {
    const m = readManifest();
    expect(m.name).toBe("MontGoWork");
    expect(m.short_name).toBeTruthy();
    expect(m.description).toBeTruthy();
    expect(m.start_url).toBe("/");
    expect(m.display).toBe("standalone");
  });

  it("declares background_color and theme_color", () => {
    const m = readManifest();
    expect(typeof m.background_color).toBe("string");
    expect(typeof m.theme_color).toBe("string");
    // theme_color must be a hex color
    expect(m.theme_color as string).toMatch(/^#[0-9a-fA-F]{6}$/);
  });

  it("declares 192 + 512 icons", () => {
    const m = readManifest();
    const icons = m.icons as Array<{ src: string; sizes: string; type: string }>;
    expect(Array.isArray(icons)).toBe(true);
    const sizes = icons.map((i) => i.sizes);
    expect(sizes).toContain("192x192");
    expect(sizes).toContain("512x512");
    for (const icon of icons) {
      expect(icon.src).toMatch(/^\//);
      expect(icon.type).toBeTruthy();
    }
  });
});
