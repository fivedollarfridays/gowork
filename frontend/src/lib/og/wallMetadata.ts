/**
 * Spotlight invention #7 (W4 Driver D) — wallMetadata.
 *
 * Per-chapter Next.js `Metadata` builder for The Wall. Resolves the right
 * OG / Twitter image URL pointing at our dynamic `/api/og/[chapter]`
 * route, with an optional locale param.
 *
 * # Why this lives in a helper module
 *
 * `app/page.tsx` is "use client" (the Wall is a fully-interactive
 * scrollytelling page). Next.js does not let `generateMetadata` ship from
 * a client module. So consumers (a future server-side wrapper, a
 * `chapter/[n]` route, the press-kit static export) call this helper from
 * server components. Keeping the resolver pure means the same call works
 * in tests, in scripts, and in the Edge runtime.
 *
 * # The contract
 *
 * - `buildWallMetadata({ chapter, locale })` returns a `Metadata` shape
 *   with openGraph + twitter both pointing at `/api/og/[N]?locale=es` or
 *   `/api/og/default`.
 * - `chapterFragmentToOgImage(fragment)` resolves a URL fragment like
 *   `#chapter-7` to its OG image URL — used by social-share buttons that
 *   read `window.location.hash`.
 * - `hreflangFor({ chapter })` declares the en + es alternates.
 *
 * Honest uncertainty (C5): we assume `NEXT_PUBLIC_SITE_URL` is set in
 * production to the canonical origin. In tests / preview the helper
 * falls back to relative paths (no leading origin) so consumers can
 * concatenate as needed.
 */

import type { Metadata } from "next";
import type { ChapterNumber } from "./cardComposer";

const DEFAULT_PATH = "/api/og/default";

/**
 * Build the OG/Twitter image URL for a given (chapter, locale).
 * Returns a path-relative URL — Next will absolutize against
 * `metadataBase` from the root layout.
 */
export function ogImageUrl(args?: {
  chapter?: ChapterNumber | null;
  locale?: string;
}): string {
  const chapter = args?.chapter ?? null;
  const locale = args?.locale ?? "en";
  const path = chapter === null ? DEFAULT_PATH : `/api/og/${chapter}`;
  return locale === "es" ? `${path}?locale=es` : path;
}

/** Map a URL fragment (`#chapter-7`) to the right OG image URL. */
export function chapterFragmentToOgImage(fragment: string): string {
  if (!fragment) return DEFAULT_PATH;
  const normalized = fragment.startsWith("#") ? fragment.slice(1) : fragment;
  const match = normalized.match(/^chapter-(\d+)$/);
  if (!match) return DEFAULT_PATH;
  const n = Number.parseInt(match[1] ?? "0", 10);
  if (!Number.isFinite(n) || n < 1 || n > 10) return DEFAULT_PATH;
  return `/api/og/${n}`;
}

interface BuildWallMetadataArgs {
  chapter?: ChapterNumber | null;
  locale?: string;
}

const SITE_NAME = "GoWork";
const SITE_TAGLINE = "Workforce infrastructure for any American city.";

/** Build a Next.js `Metadata` object pointing at the right OG card. */
export function buildWallMetadata(args: BuildWallMetadataArgs = {}): Metadata {
  const { chapter, locale = "en" } = args;
  const url = ogImageUrl({ chapter: chapter ?? null, locale });
  const altText =
    chapter !== null && chapter !== undefined
      ? `${SITE_NAME} — Chapter ${chapter}`
      : `${SITE_NAME} — ${SITE_TAGLINE}`;

  return {
    openGraph: {
      type: "website",
      siteName: SITE_NAME,
      title: `${SITE_NAME} — ${SITE_TAGLINE}`,
      description: SITE_TAGLINE,
      images: [
        {
          url,
          width: 1200,
          height: 630,
          alt: altText,
        },
      ],
      locale: locale === "es" ? "es_ES" : "en_US",
    },
    twitter: {
      card: "summary_large_image",
      title: `${SITE_NAME} — ${SITE_TAGLINE}`,
      description: SITE_TAGLINE,
      images: [url],
    },
  };
}

/** Declare en + es hreflang alternates for the Wall's metadata. */
export function hreflangFor(args: BuildWallMetadataArgs = {}): {
  languages: Record<string, string>;
} {
  const { chapter } = args;
  const enUrl = ogImageUrl({ chapter: chapter ?? null, locale: "en" });
  const esUrl = ogImageUrl({ chapter: chapter ?? null, locale: "es" });
  return {
    languages: {
      en: enUrl,
      es: esUrl,
    },
  };
}
