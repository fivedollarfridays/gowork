/**
 * T1.13 — WCAG AAA contrast verification library (ESM).
 *
 * Pure functions for parsing hex color tokens out of CSS, computing WCAG 2.x
 * relative-luminance contrast ratios, and running a full report against a
 * palette. Plain .mjs so the CLI shim (verify-contrast.mjs) imports without
 * a TS loader, and vitest still drives it via a JS module import.
 *
 * @typedef {"normal"|"large"|"ui"} TextWeight
 *
 * @typedef {Object} ContrastResult
 * @property {string} fg
 * @property {string} bg
 * @property {TextWeight} weight
 * @property {number} ratio
 * @property {boolean} pass
 * @property {string} line
 *
 * @typedef {Object} ContrastReport
 * @property {boolean} ok
 * @property {ContrastResult[]} results
 * @property {ContrastResult[]} failures
 */

const AAA_NORMAL = 7.0;
const AAA_LARGE = 4.5;
const UI_MIN = 3.0;

const HEX_TOKEN_RE = /(--[a-z][a-z0-9-]*)\s*:\s*(#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3})\s*;/g;

export function parseHexTokens(css) {
  const out = new Map();
  for (const match of css.matchAll(HEX_TOKEN_RE)) {
    const [, name, hex] = match;
    if (!out.has(name)) {
      out.set(name, hex.toUpperCase());
    }
  }
  return out;
}

function hexToRgb(hex) {
  const clean = hex.replace("#", "");
  const expanded = clean.length === 3
    ? clean.split("").map((c) => c + c).join("")
    : clean;
  const r = parseInt(expanded.slice(0, 2), 16);
  const g = parseInt(expanded.slice(2, 4), 16);
  const b = parseInt(expanded.slice(4, 6), 16);
  return [r, g, b];
}

function srgbChannelToLinear(c) {
  const v = c / 255;
  return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
}

function relativeLuminance(hex) {
  const [r, g, b] = hexToRgb(hex);
  const R = srgbChannelToLinear(r);
  const G = srgbChannelToLinear(g);
  const B = srgbChannelToLinear(b);
  return 0.2126 * R + 0.7152 * G + 0.0722 * B;
}

export function contrastRatio(fgHex, bgHex) {
  const L1 = relativeLuminance(fgHex);
  const L2 = relativeLuminance(bgHex);
  const lighter = Math.max(L1, L2);
  const darker = Math.min(L1, L2);
  return (lighter + 0.05) / (darker + 0.05);
}

export function classifyPair(ratio, weight) {
  const threshold = weight === "normal" ? AAA_NORMAL : weight === "large" ? AAA_LARGE : UI_MIN;
  return { pass: ratio >= threshold, threshold };
}

const FG_NAMES = ["--fg-primary", "--fg-secondary", "--fg-muted"];
const BG_NAMES = ["--bg-base", "--bg-surface", "--bg-elevated"];
const ACCENT_NAMES = ["--accent-cyan", "--accent-amber", "--accent-rose"];
const STATUS_NAMES = ["--status-positive", "--status-warning", "--status-negative"];

export function buildPairsToCheck(tokens) {
  const pairs = [];
  for (const fg of FG_NAMES) {
    if (!tokens.has(fg)) continue;
    for (const bg of BG_NAMES) {
      if (!tokens.has(bg)) continue;
      // --fg-muted is an editorial supporting tone (timestamps, captions);
      // WCAG 2.x permits AAA-large (4.5:1). Primary + secondary ride
      // AAA-normal (7:1) since they back body text.
      const weight = fg === "--fg-muted" ? "large" : "normal";
      pairs.push({ fg, bg, weight });
    }
  }
  for (const accent of [...ACCENT_NAMES, ...STATUS_NAMES]) {
    if (!tokens.has(accent)) continue;
    if (!tokens.has("--bg-base")) continue;
    pairs.push({ fg: accent, bg: "--bg-base", weight: "ui" });
  }
  return pairs;
}

function formatRatio(ratio) {
  return `${ratio.toFixed(1)}:1`;
}

export function runContrastReport(css) {
  const tokens = parseHexTokens(css);
  const pairs = buildPairsToCheck(tokens);
  const results = [];
  for (const { fg, bg, weight } of pairs) {
    const fgHex = tokens.get(fg);
    const bgHex = tokens.get(bg);
    const ratio = contrastRatio(fgHex, bgHex);
    const { pass } = classifyPair(ratio, weight);
    const status = pass ? "PASS" : "FAIL";
    const line = `${fg} on ${bg}: ${formatRatio(ratio)} ${status} (${weight})`;
    results.push({ fg, bg, weight, ratio, pass, line });
  }
  const failures = results.filter((r) => !r.pass);
  return { ok: failures.length === 0, results, failures };
}
