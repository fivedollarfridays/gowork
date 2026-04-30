/**
 * Z-stack tokens (Wave 2 — cross-driver integration).
 *
 * Driver C shipped overlay components (CookieBanner, PWAInstallPrompt,
 * StallAlertBanner, SkipToContent, CursorFlashlight, AriaLiveRegion) using
 * Tailwind z-index utilities (`z-50`, `z-[55]` etc). Without a token
 * hierarchy, two overlays at z-[55] (CookieBanner + PWAInstallPrompt) collide.
 *
 * This token namespace declares the canonical hierarchy. Every overlay
 * surface SHOULD reference these tokens (via `var(--z-*)`) instead of
 * literal numbers.
 *
 * Hierarchy contract (highest-on-top):
 *   --z-skip-link:        100 — keyboard users land here first; never occluded
 *   --z-modal:             80 — modal dialogs (W2/W3 reserved)
 *   --z-toast:             70 — transient announcements
 *   --z-header:            50 — sticky header
 *   --z-banner:            40 — stall-alert banner BELOW header (under chrome)
 *   --z-pwa-prompt:        30 — install prompt (below banner)
 *   --z-cookie:            30 — cookie disclosure (below banner; siblings ok)
 *   --z-cursor-flashlight:  5 — overlay above content, below chrome
 *   --z-content:            1 — default page content
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const LAYOUT_CSS = readFileSync(
  join(process.cwd(), "src/app/styles/tokens/layout.css"),
  "utf8",
);

describe("z-index token hierarchy", () => {
  const TOKENS: Array<[string, string]> = [
    ["--z-skip-link", "100"],
    ["--z-modal", "80"],
    ["--z-toast", "70"],
    ["--z-header", "50"],
    ["--z-banner", "40"],
    ["--z-pwa-prompt", "30"],
    ["--z-cookie", "30"],
    ["--z-cursor-flashlight", "5"],
    ["--z-content", "1"],
  ];

  for (const [token, value] of TOKENS) {
    it(`declares ${token}: ${value}`, () => {
      const re = new RegExp(`${token}\\s*:\\s*${value}\\s*;`);
      expect(LAYOUT_CSS).toMatch(re);
    });
  }

  it("documents the hierarchy in a comment block", () => {
    expect(LAYOUT_CSS.toLowerCase()).toMatch(/z-index|z-stack|stacking/);
  });

  it("orders skip-link strictly above header", () => {
    const skip = parseInt(LAYOUT_CSS.match(/--z-skip-link\s*:\s*(\d+)/)?.[1] ?? "0", 10);
    const header = parseInt(LAYOUT_CSS.match(/--z-header\s*:\s*(\d+)/)?.[1] ?? "0", 10);
    expect(skip).toBeGreaterThan(header);
  });

  it("orders header strictly above banner so chrome wins", () => {
    const header = parseInt(LAYOUT_CSS.match(/--z-header\s*:\s*(\d+)/)?.[1] ?? "0", 10);
    const banner = parseInt(LAYOUT_CSS.match(/--z-banner\s*:\s*(\d+)/)?.[1] ?? "0", 10);
    expect(header).toBeGreaterThan(banner);
  });
});
