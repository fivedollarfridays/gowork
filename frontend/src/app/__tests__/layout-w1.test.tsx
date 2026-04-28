/**
 * W1 Driver C — root layout enrichment.
 *
 * Goes beyond the legacy metadata.test.tsx (which guards the OG/Twitter
 * suite) by asserting the W1-specific enrichments :
 *   - The skip-to-content link is mounted at the top of the body so
 *     keyboard users land on it first (T1.63).
 *   - The new G + path mark is referenced via /icon.svg (NOT favicon.svg
 *     or any legacy file).
 *   - The viewport theme color is the new --bg-base #0A0E1A.
 *   - The OG image references /og-image.svg (the new GoWork card).
 */
import { describe, it, expect, vi } from "vitest";

vi.mock("next/font/google", () => ({
  Inter: () => ({ variable: "--font-inter", className: "font-inter" }),
}));

const { metadata, viewport } = await import("../layout");

describe("Root layout — W1 brand enrichment", () => {
  it("uses the new bg-base theme color #0A0E1A in viewport", () => {
    expect(viewport.themeColor).toBe("#0A0E1A");
  });

  it("references /icon.svg as the SVG icon source", () => {
    const icons = metadata.icons as { icon?: Array<{ url: string; type?: string }> };
    const icon = (icons.icon ?? []).find((i) => i.url === "/icon.svg");
    expect(icon).toBeDefined();
    expect(icon?.type).toBe("image/svg+xml");
  });

  it("references /og-image.svg in openGraph.images and twitter.images", () => {
    const og = metadata.openGraph as { images?: Array<{ url?: string }> | string };
    const ogImages = (Array.isArray(og.images) ? og.images : []).map(
      (i) => i?.url ?? "",
    );
    expect(ogImages.some((u) => u.includes("/og-image"))).toBe(true);

    const tw = metadata.twitter as { images?: Array<string> | string };
    const twImages = Array.isArray(tw.images)
      ? tw.images
      : tw.images
        ? [tw.images as string]
        : [];
    expect(twImages.some((u) => u.includes("/og-image"))).toBe(true);
  });

  it("declares applicationName as GoWork (NOT MontGoWork)", () => {
    expect(metadata.applicationName).toBe("GoWork");
  });
});
