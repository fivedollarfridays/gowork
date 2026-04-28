import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";
import { FONT_AXES } from "../lib/wall/tokens";

/**
 * T1.102 — Variable font axis tokens (slant + italic + optical-size).
 * T1.103 — Drop cap CSS utility.
 *
 * Brief mentions the optical-size axis only; T1.102 adds the slant axis so
 * editorial typography (drop caps, pull quotes) renders with magazine-grade
 * polish. T1.103 adds the .dropcap::first-letter rule for chapter intros.
 */

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..");
const TYPOGRAPHY_CSS = path.resolve(FRONTEND_ROOT, "src/app/styles/tokens/typography.css");

function read(): string {
  return fs.readFileSync(TYPOGRAPHY_CSS, "utf-8");
}

describe("T1.102 — variable font axis CSS tokens", () => {
  const css = read();

  it.each([
    ["--font-axis-wght-display", "900"],
    ["--font-axis-wght-body", "400"],
    ["--font-axis-opsz-display", "32"],
    ["--font-axis-opsz-body", "14"],
    ["--font-axis-slnt-italic", "-10"],
  ])("declares %s = %s", (token, value) => {
    const re = new RegExp(`${token}\\s*:\\s*${value}\\s*;`);
    expect(css).toMatch(re);
  });

  it(".italic-axis utility uses oblique slant for Inter Variable", () => {
    expect(css).toMatch(/\.italic-axis[\s\S]*font-style:\s*oblique\s*-10deg/);
  });
});

describe("T1.102 — TS export FONT_AXES", () => {
  it("exposes wghtDisplay/wghtBody/opszDisplay/opszBody/slntItalic", () => {
    expect(FONT_AXES.wghtDisplay).toBe(900);
    expect(FONT_AXES.wghtBody).toBe(400);
    expect(FONT_AXES.opszDisplay).toBe(32);
    expect(FONT_AXES.opszBody).toBe(14);
    expect(FONT_AXES.slntItalic).toBe(-10);
  });
});

describe("T1.103 — drop cap utility", () => {
  const css = read();

  it(".dropcap::first-letter rule defined", () => {
    expect(css).toMatch(/\.dropcap::first-letter\s*\{/);
  });

  it("drop cap floats left + uses cyan accent", () => {
    const m = css.match(/\.dropcap::first-letter\s*\{([^}]+)\}/);
    expect(m).not.toBeNull();
    expect(m![1]).toMatch(/float:\s*left/);
    expect(m![1]).toMatch(/var\(--accent-cyan\)/);
  });

  it("drop cap uses display weight + opsz axis", () => {
    const m = css.match(/\.dropcap::first-letter\s*\{([^}]+)\}/);
    expect(m![1]).toMatch(/font-variation-settings/);
    expect(m![1]).toMatch(/wght/);
    expect(m![1]).toMatch(/opsz/);
  });
});
