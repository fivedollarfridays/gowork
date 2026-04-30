/**
 * Light-mode polish — locks the always-dark editorial surfaces against
 * the global theme toggle.
 *
 * Several editorial surfaces in the homepage are intentionally rendered
 * with a navy gradient backdrop in BOTH themes (Ch05 plan-cards, Ch05
 * expanded-card overlay, Ch07 cliff controls panel, Ch04 map chips that
 * sit over the perma-dark Mapbox canvas). When the user toggles to light
 * mode, `var(--fg-primary)` flips to navy ink and the inner text becomes
 * dark-on-dark — invisible.
 *
 * The fix locks each of those surfaces' text to literal cream/muted-cream
 * hex values so they stay legible regardless of the global theme. This
 * test reads the stylesheet sources and asserts the locked overrides are
 * present, so a future refactor can't silently regress them.
 *
 * See feat/light-mode-polish PR for full per-bug breakdown.
 */
import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";

const FRONTEND_ROOT = path.resolve(__dirname, "..", "..", "..", "..");
const HOME_CHAPTERS_CSS = path.resolve(
  FRONTEND_ROOT,
  "src/app/styles/home-chapters.css",
);
const HOME_VELOCITY_CSS = path.resolve(
  FRONTEND_ROOT,
  "src/app/styles/home-velocity.css",
);

const homeChaptersCss = fs.readFileSync(HOME_CHAPTERS_CSS, "utf8");
const homeVelocityCss = fs.readFileSync(HOME_VELOCITY_CSS, "utf8");

describe("light-mode polish — Ch05 plan cards locked-light text", () => {
  // The ch05-card surface is a dark navy gradient (`linear-gradient(160deg,
  // #2a1d09 0%, #15203a 100%)` etc.). Its text MUST be locked-cream because
  // a theme-flipped fg color would render navy-on-navy.
  it("declares a [data-theme='light'] override that locks card title to cream", () => {
    expect(homeChaptersCss).toMatch(
      /\[data-theme="light"\][^{]*\.ch05-card[^{]*h3[^{]*\{[^}]*color:\s*#F5F3EE/i,
    );
  });

  it("declares a [data-theme='light'] override that locks card body to muted cream", () => {
    expect(homeChaptersCss).toMatch(
      /\[data-theme="light"\][^{]*\.ch05-card[^{]*p[^{]*\{[^}]*color:\s*#A4B3C7/i,
    );
  });

  it("declares a [data-theme='light'] override for pc-num + pc-foot (muted)", () => {
    expect(homeChaptersCss).toMatch(
      /\[data-theme="light"\][^{]*\.ch05-card[^{]*\.pc-num[^{]*\{[^}]*color:\s*#8696A8/i,
    );
    expect(homeChaptersCss).toMatch(
      /\[data-theme="light"\][^{]*\.ch05-card[^{]*\.pc-foot[^{]*\{[^}]*color:\s*#8696A8/i,
    );
  });
});

describe("light-mode polish — Ch05 expanded-card overlay locked-light text", () => {
  // Same logic as the in-deck cards: dark gradient surface + cream text.
  // The overlay portals to document.body so it picks up the toggle's
  // [data-theme] state on <html>.
  it("declares a [data-theme='light'] override that locks overlay title to cream", () => {
    expect(homeVelocityCss).toMatch(
      /\[data-theme="light"\][^{]*\.ch05-overlay__card[^{]*h3[^{]*\{[^}]*color:\s*#F5F3EE/i,
    );
  });

  it("declares a [data-theme='light'] override that locks overlay body to muted cream", () => {
    expect(homeVelocityCss).toMatch(
      /\[data-theme="light"\][^{]*\.ch05-overlay__card[^{]*p[^{]*\{[^}]*color:\s*#A4B3C7/i,
    );
  });

  it("declares a [data-theme='light'] override that locks overlay bullets to cream", () => {
    expect(homeVelocityCss).toMatch(
      /\[data-theme="light"\][^{]*\.ch05-overlay__bullets\s+li[^{]*\{[^}]*color:\s*#F5F3EE/i,
    );
  });
});

describe("light-mode polish — Ch04 map chip text (perma-dark backdrop)", () => {
  // The map is locked dark via Chapter04TheMap.mount.ts readStyleUrl().
  // Therefore the legend / compass / attribution / stat-row chips that
  // sit over the dark map need locked-light text, NOT theme-flipping
  // tokens that turn navy-on-navy in light mode.
  it("locks .ch04-legend text in light mode (cream)", () => {
    expect(homeChaptersCss).toMatch(
      /\[data-theme="light"\][^{]*\.ch04-legend\s*\{[^}]*color:\s*#A4B3C7/i,
    );
  });

  it("locks .ch04-compass + chip values in light mode", () => {
    expect(homeChaptersCss).toMatch(
      /\[data-theme="light"\][^{]*\.ch04-compass[^{]*\{[^}]*color:\s*(#A4B3C7|#F5F3EE)/i,
    );
  });

  it("locks .ch04-stat-row stat values in light mode (cream)", () => {
    expect(homeChaptersCss).toMatch(
      /\[data-theme="light"\][^{]*\.ch04-stat__v[^{]*\{[^}]*color:\s*#F5F3EE/i,
    );
  });
});

describe("light-mode polish — Ch07 cliff controls panel (perma-dark glass)", () => {
  // The CliffControls component renders an inline-styled dark glass
  // panel (`linear-gradient(160deg, rgba(15, 23, 41, 0.65) 0%,
  // rgba(10, 14, 26, 0.55) 100%)`). The labels MUST stay cream/muted in
  // light mode for the same reason as the ch05 cards.
  it("declares a [data-theme='light'] override for the cliff controls labels", () => {
    expect(homeChaptersCss).toMatch(
      /\[data-theme="light"\][^{]*\.ch07-controls[^{]*\.r-k[^{]*\{[^}]*color:\s*#8696A8/i,
    );
  });

  it("declares a [data-theme='light'] override for the cliff controls value (gross/total)", () => {
    expect(homeChaptersCss).toMatch(
      /\[data-theme="light"\][^{]*\.ch07-controls[^{]*\.r-v[^{]*\{[^}]*color:\s*#F5F3EE/i,
    );
  });

  it("scopes --fg-* tokens inside .ch07-controls to dark-mode literals (defeats inline-style cascade)", () => {
    // CliffControls.tsx renders inline `color: var(--fg-muted)` etc. on
    // r-k / ctrl-k / segmented-control labels. Inline styles win over
    // class rules — the only way to override their color in light mode
    // is to redefine the underlying CSS variable inside the panel
    // scope. This test asserts that scoped redefinition exists.
    expect(homeChaptersCss).toMatch(
      /\[data-theme="light"\][^{]*\.ch07-controls[^{]*\{[^}]*--fg-muted:\s*#8696A8/i,
    );
    expect(homeChaptersCss).toMatch(
      /\[data-theme="light"\][^{]*\.ch07-controls[^{]*\{[^}]*--fg-primary:\s*#F5F3EE/i,
    );
  });
});

describe("light-mode polish — Ch08 mic-drop CTA pill", () => {
  // The CTA pill sits on a bright amber-rose-cyan gradient. In light mode
  // its `var(--fg-primary)` resting bg flipped to navy ink and read as a
  // black silhouette with no visible text. Lock the bg to cream literal.
  it("ch08 mic-drop CTA bg is locked to cream literal, not theme-flipping token", () => {
    // Find the rule body and assert it does NOT use var(--fg-primary)
    // for background.
    const ruleBlock = homeVelocityCss.match(
      /\.ch08-mic-drop__cta\s+a\.cta-primary\s*\{[^}]+\}/,
    );
    expect(ruleBlock).not.toBeNull();
    const body = ruleBlock?.[0] ?? "";
    expect(body).toMatch(/background:\s*#F5F3EE/i);
    expect(body).not.toMatch(/background:\s*var\(--fg-primary\)/i);
  });
});

describe("light-mode polish — Ch08 wordmark always-cream", () => {
  // The wordmark mic-drop sits over a multi-color gradient. Cream reads
  // on every gradient stop in BOTH themes, but `var(--fg-primary)` flips
  // to navy ink in light → the wordmark renders as massive black on
  // bright gradient (overpowering). Lock the wordmark surface tokens to
  // cream literals.
  it("ch08-wordmark color is locked-cream in light mode", () => {
    expect(homeVelocityCss).toMatch(
      /\[data-theme="light"\][^{]*\.ch08-wordmark[^{]*\{[^}]*color:\s*#F5F3EE/i,
    );
  });

  it("ch08-brand-icon is locked-cream in light mode", () => {
    expect(homeVelocityCss).toMatch(
      /\[data-theme="light"\][^{]*\.ch08-brand-icon[^{]*\{[^}]*color:\s*#F5F3EE/i,
    );
  });

  it("ch08-aberration glyphs locked-cream in light mode", () => {
    expect(homeVelocityCss).toMatch(
      /\[data-theme="light"\][^{]*\.ch08-aberration[^{]*\{[^}]*color:\s*#F5F3EE/i,
    );
  });
});
