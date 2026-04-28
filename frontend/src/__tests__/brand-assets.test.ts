/**
 * W1 Driver C — brand asset contract for OG and manifest.
 *
 * Asserts:
 *   - public/og-image.svg uses the GoWork wordmark (NOT MontGoWork),
 *     the cyan path mark, the locked tagline, and the dark gradient base.
 *   - public/manifest.json declares GoWork as name/short_name, the new
 *     tagline as description, theme_color = #0A0E1A (--bg-base), and
 *     keeps the established categories.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const PUBLIC = join(process.cwd(), "public");

function read(name: string): string {
  return readFileSync(join(PUBLIC, name), "utf8");
}

describe("public/og-image.svg — GoWork OG card", () => {
  const svg = read("og-image.svg");

  it("uses the 1200x630 OG canvas", () => {
    expect(svg).toMatch(/viewBox=["']0 0 1200 630["']/);
  });

  it("contains the GoWork wordmark (NOT MontGoWork)", () => {
    expect(svg).toMatch(/GoWork/);
    expect(svg).not.toMatch(/MontGoWork/);
  });

  it("contains the locked tagline", () => {
    expect(svg).toMatch(/Workforce infrastructure for any American city/);
  });

  it("uses the dark gradient base #0A0E1A → #0F1729", () => {
    expect(svg).toMatch(/#0A0E1A/i);
    expect(svg).toMatch(/#0F1729/i);
  });

  it("references the cyan path accent", () => {
    expect(svg).toMatch(/#22D3EE/i);
  });
});

describe("public/manifest.json — GoWork PWA manifest", () => {
  const manifest = JSON.parse(read("manifest.json")) as Record<string, unknown>;

  it("uses GoWork as name and short_name", () => {
    expect(manifest.name).toBe("GoWork");
    expect(manifest.short_name).toBe("GoWork");
  });

  it("uses the locked tagline as description", () => {
    expect(manifest.description).toMatch(
      /Workforce infrastructure for any American city/,
    );
  });

  it("uses the new theme color (--bg-base #0A0E1A)", () => {
    expect(manifest.theme_color).toBe("#0A0E1A");
  });

  it("keeps the established categories", () => {
    expect(manifest.categories).toEqual([
      "productivity",
      "education",
      "social",
    ]);
  });

  it("declares the maskable icon variant", () => {
    const icons = manifest.icons as Array<Record<string, string>>;
    const maskable = icons.find((i) => i.purpose === "maskable");
    expect(maskable).toBeDefined();
  });
});
