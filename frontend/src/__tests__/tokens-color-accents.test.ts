import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

/**
 * T1.11 — Accent + status tokens with color-mix() shade variants.
 *
 * 7 base accent/status tokens + --accent-current alias + 5 shade variants per
 * accent (cyan, amber, rose) = at least 15 color-mix() shade tokens.
 * Hex fallbacks live in @supports not (color: oklch(...)).
 */

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..");
const COLORS_CSS = path.resolve(FRONTEND_ROOT, "src/app/styles/tokens/colors.css");

function read(): string {
  return fs.readFileSync(COLORS_CSS, "utf-8");
}

describe("T1.11 — accent + status base tokens", () => {
  const css = read();

  it.each([
    ["--accent-cyan", "#22D3EE"],
    ["--accent-amber", "#F59E0B"],
    ["--accent-rose", "#FB7185"],
    ["--status-positive", "#34D399"],
    ["--status-warning", "#FBBF24"],
    ["--status-negative", "#FB7185"],
  ])("defines %s with hex %s", (token, hex) => {
    expect(css).toMatch(new RegExp(`${token}\\s*:\\s*${hex}`, "i"));
  });

  it("defines --accent-current as a live-shifting alias", () => {
    expect(css).toMatch(/--accent-current/);
  });
});

describe("T1.11 — color-mix() shade variants", () => {
  const css = read();

  it.each([
    ["--accent-cyan-100"],
    ["--accent-cyan-300"],
    ["--accent-cyan-500"],
    ["--accent-cyan-700"],
    ["--accent-cyan-900"],
    ["--accent-amber-100"],
    ["--accent-amber-300"],
    ["--accent-amber-500"],
    ["--accent-amber-700"],
    ["--accent-amber-900"],
    ["--accent-rose-100"],
    ["--accent-rose-300"],
    ["--accent-rose-500"],
    ["--accent-rose-700"],
    ["--accent-rose-900"],
  ])("defines shade variant %s", (token) => {
    expect(css).toContain(token);
  });

  it("at least 15 color-mix() invocations across shade tokens", () => {
    const matches = css.match(/color-mix\(/g) ?? [];
    expect(matches.length).toBeGreaterThanOrEqual(15);
  });
});

describe("T1.11 — graceful degradation for non-color-mix browsers", () => {
  const css = read();

  it("provides @supports not (color-mix(...)) hex fallback block", () => {
    expect(css).toMatch(/@supports\s+not\s*\(color:\s*color-mix/);
  });
});

describe("T1.11 — colors.css size budget", () => {
  it("colors.css <340 lines (bumped 2026-05-01 for demo-grade dark-mode `.text-secondary` cyan override + commentary)", () => {
    const lines = read().split("\n").length;
    expect(lines).toBeLessThan(340);
  });
});
