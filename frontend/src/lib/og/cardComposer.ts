/**
 * Spotlight invention #1 (W4 Driver D) — cardComposer.
 *
 * Pure-function composition of the OG card React tree from
 * (chapterIndex, locale). Single source of truth consumed by:
 *
 *   1. `app/api/og/[chapter]/route.ts` — Edge runtime ImageResponse
 *      generator. Each Wall chapter (1..10) gets its own dynamic OG
 *      card at /api/og/N — Twitter / X / LinkedIn / Slack unfurls show
 *      the chapter-specific share image, not the global fallback.
 *   2. `app/api/og/default/route.ts` — site-wide GoWork fallback card.
 *   3. Future email digest send-time card (W5 press-kit).
 *   4. Future static press-kit export (W5).
 *
 * # Why a pure module
 *
 * Satori (the renderer behind @vercel/og) does not run React effects or
 * hooks — it just walks a JSX/element tree and emits SVG-then-PNG. So a
 * pure composition function is a perfect fit:
 *   - No fetch, no env reads, no async work — composes anywhere.
 *   - The same call site works in an Edge route AND a Node test AND a
 *     local CLI (e.g. press-kit static export script).
 *   - Locale + chapter index are the only inputs; the translations file
 *     is bundled.
 *
 * # Locale fallback
 *
 * When `locale` is not 'en' or 'es' we fall through to English. We never
 * crash on an unknown locale — judges sharing a /?locale=fr URL still
 * get a beautiful OG card.
 *
 * # Accent palette
 *
 * Each chapter is keyed to a phase of the day → an accent token (Driver
 * A's `timeOfDayPalette` Spotlight). Ch1 is "morning" amber-cyan, Ch7 is
 * "afternoon" cyan, Ch10 is "dusk" rose, etc. — gives the card pack
 * editorial coherence without being random.
 */

import React from "react";
import en from "../translations/en.json";
import es from "../translations/es.json";
import type { AccentToken } from "../wall/timeOfDayPalette";

/** Twitter Card / OG standard dimensions. */
export const CARD_WIDTH = 1200;
export const CARD_HEIGHT = 630;

/** Wall chapters are 1..10 (W3 final). */
export type ChapterNumber = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10;

/** Supported locales. Anything else falls back to 'en'. */
export type SupportedLocale = "en" | "es";

/** Per-chapter accent assignment — gives the OG card pack editorial
 *  coherence. Mirrors W4 timeOfDayPalette tokens. */
const CHAPTER_ACCENTS: Record<ChapterNumber, AccentToken> = {
  1: "amber", // Continental dawn — the awakening question.
  2: "cyan", // City arrival — Trinity Metro cyan.
  3: "blue", // Neighborhood — community blue.
  4: "rose", // The Wall — the barrier flush.
  5: "indigo", // The Labyrinth — disorientation depth.
  6: "amber", // The Math — receipt amber.
  7: "cyan", // The Path — Trinity Metro routing.
  8: "blue", // The Graph — constellation blue.
  9: "amber", // Any City — sunrise broadcast.
  10: "rose", // Find Your Path — invitation rose.
};

/** Hex equivalents for accent tokens — Satori does not parse OKLCH yet
 *  reliably, and the OG card rasterizes once and lives forever, so a
 *  fixed sRGB lookup is the right call. */
const ACCENT_HEX: Record<AccentToken, string> = {
  amber: "#F5A623",
  cyan: "#22D3EE",
  blue: "#3B82F6",
  rose: "#FB7185",
  indigo: "#6366F1",
};

/** Brand palette — kept inline so the card composes without pulling in
 *  the larger token system at build time. */
const BG_DEEP = "#0A0E1A";
const BG_SURFACE = "#0F1729";
const FG_PRIMARY = "#F5F3EE";
const FG_SECONDARY = "#94A3B8";
const FG_TERTIARY = "#64748B";

/** Resolved meta returned alongside the React tree. */
export interface CardMeta {
  title: string;
  hero: string;
  accent: AccentToken;
  accentHex: string;
}

/** Composed result — `tree` is the JSX/element root for ImageResponse. */
export interface ComposedCard {
  tree: React.ReactElement;
  meta: CardMeta;
}

type TranslationsTree = typeof en;

function resolveLocaleBundle(locale: string): TranslationsTree {
  if (locale === "es") return es as TranslationsTree;
  return en;
}

function chapterKey(n: ChapterNumber): string {
  return n < 10 ? `chapter0${n}` : `chapter${n}`;
}

/** Loose chapter-row shape — translations have heterogeneous keys per
 *  chapter (Ch8 has nested `barrierLabels`, others don't). We accept
 *  arbitrary string-keyed values and only narrow to strings on read. */
type ChapterRow = Record<string, unknown>;

function readString(row: ChapterRow, key: string): string | undefined {
  const value = row[key];
  return typeof value === "string" ? value : undefined;
}

/** Look up the (title, hero) tuple from translations + the accent token. */
export function resolveChapterMeta(
  chapter: ChapterNumber,
  locale: string,
): CardMeta {
  const bundle = resolveLocaleBundle(locale);
  const wall = (bundle as unknown as { wall: Record<string, ChapterRow> }).wall;
  const ch = wall[chapterKey(chapter)] ?? {};

  // Some W2/W3 chapters use `body` / `lede` / `editorial` instead of `hero`.
  // Fall through in priority order so every chapter has a non-empty hero.
  const hero =
    readString(ch, "hero") ??
    readString(ch, "heroQuestion") ??
    readString(ch, "lede") ??
    readString(ch, "editorial") ??
    readString(ch, "body") ??
    "";
  const title = readString(ch, "title") ?? `GoWork — Chapter ${chapter}`;
  const accent = CHAPTER_ACCENTS[chapter];

  return {
    title,
    hero,
    accent,
    accentHex: ACCENT_HEX[accent],
  };
}

/** Card-tree builder shared by chapter + default cards. */
function buildCardTree(args: {
  title: string;
  hero: string;
  accentHex: string;
  footer: string;
}): React.ReactElement {
  const { title, hero, accentHex, footer } = args;

  const containerStyle: React.CSSProperties = {
    width: `${CARD_WIDTH}px`,
    height: `${CARD_HEIGHT}px`,
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    padding: "80px",
    background: `linear-gradient(135deg, ${BG_DEEP} 0%, ${BG_SURFACE} 100%)`,
    fontFamily: "Inter, system-ui, sans-serif",
    color: FG_PRIMARY,
  };

  const brandRowStyle: React.CSSProperties = {
    display: "flex",
    alignItems: "center",
    gap: "16px",
  };

  const accentDotStyle: React.CSSProperties = {
    width: "20px",
    height: "20px",
    borderRadius: "999px",
    background: accentHex,
  };

  const wordmarkStyle: React.CSSProperties = {
    fontSize: "32px",
    fontWeight: 800,
    letterSpacing: "-0.02em",
    color: FG_PRIMARY,
  };

  const titleStyle: React.CSSProperties = {
    fontSize: "36px",
    fontWeight: 600,
    color: accentHex,
    letterSpacing: "-0.01em",
  };

  const heroStyle: React.CSSProperties = {
    fontSize: "72px",
    fontWeight: 800,
    lineHeight: 1.05,
    letterSpacing: "-0.04em",
    color: FG_PRIMARY,
    marginTop: "24px",
    marginBottom: "0",
    maxWidth: "1040px",
  };

  const accentBarStyle: React.CSSProperties = {
    width: "120px",
    height: "6px",
    background: accentHex,
    borderRadius: "999px",
    marginTop: "32px",
  };

  const footerStyle: React.CSSProperties = {
    fontSize: "22px",
    color: FG_TERTIARY,
    fontWeight: 500,
    display: "flex",
    alignItems: "center",
    gap: "10px",
  };

  const taglineStyle: React.CSSProperties = {
    fontSize: "24px",
    color: FG_SECONDARY,
    fontWeight: 400,
    marginTop: "12px",
  };

  return React.createElement(
    "div",
    { style: containerStyle },
    React.createElement(
      "div",
      { style: brandRowStyle },
      React.createElement("div", { style: accentDotStyle }),
      React.createElement("div", { style: wordmarkStyle }, "GoWork"),
    ),
    React.createElement(
      "div",
      { style: { display: "flex", flexDirection: "column" } },
      React.createElement("div", { style: titleStyle }, title),
      React.createElement("div", { style: heroStyle }, hero),
      React.createElement("div", { style: accentBarStyle }),
      React.createElement(
        "div",
        { style: taglineStyle },
        "Workforce infrastructure for any American city.",
      ),
    ),
    React.createElement("div", { style: footerStyle }, footer),
  );
}

/** Compose a per-chapter OG card. Returns a React element tree + meta. */
export function composeChapterCard(
  chapter: ChapterNumber,
  locale: string,
): ComposedCard {
  const meta = resolveChapterMeta(chapter, locale);
  const footer =
    locale === "es"
      ? `GoWork · Capítulo ${chapter} · Fort Worth, TX`
      : `GoWork · Chapter ${chapter} · Fort Worth, TX`;
  const tree = buildCardTree({
    title: meta.title,
    hero: meta.hero,
    accentHex: meta.accentHex,
    footer,
  });
  return { tree, meta };
}

/** Compose the site-wide default OG card (used for /api/og/default). */
export function composeDefaultCard(locale: string): ComposedCard {
  const isEs = locale === "es";
  const title = isEs ? "GoWork — El Muro" : "GoWork — The Wall";
  const hero = isEs
    ? "¿Qué se interpone entre tú y un empleo?"
    : "What's standing between you and a job?";
  const accent: AccentToken = "cyan";
  const accentHex = ACCENT_HEX[accent];
  const footer = isEs
    ? "GoWork · Fort Worth, TX · abril de 2026"
    : "GoWork · Fort Worth, TX · April 2026";
  const tree = buildCardTree({ title, hero, accentHex, footer });
  return { tree, meta: { title, hero, accent, accentHex } };
}
