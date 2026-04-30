/**
 * T13.117 — Sitemap (Next.js App Router convention).
 * polish-2 T52 — extended with 8 chapter anchors + es-locale alts.
 *
 * Next.js renders this module at request time as `/sitemap.xml`.
 *
 * Route inventory rationale:
 *   - `/`, `/assess` are publicly discoverable hackathon-submission entry
 *     points and belong in the sitemap.
 *   - `/?chapter=N` (1..8) — deep-link to a specific homepage chapter.
 *     Google + Bing can surface chapter-specific share cards (T51 OG).
 *   - Every public entry declares an `alternates.languages.es` to wire
 *     hreflang for the Spanish-locale users.
 *   - Worker-only routes (`/daily`, `/plan`, `/jobs`, `/documents/*`,
 *     `/appointments`, `/credit`) are only reachable from a session URL or
 *     advisor flow. We deliberately omit them so crawlers don't burn
 *     auth-failure cycles on screens that require state.
 *   - Token-gated routes (`/feedback/[token]`, `/shared/[token]`) MUST NOT
 *     be enumerated — the tokens are unguessable secrets and indexing them
 *     would also defeat the share-link redaction work in T13.71.
 *   - Admin routes (`/admin/*`) are blocked here AND in robots.ts.
 *
 * The site URL is read from `NEXT_PUBLIC_SITE_URL` (matches
 * `app/layout.tsx`'s default of `https://gowork.example`).
 */
import type { MetadataRoute } from "next";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://gowork.example";

const TOTAL_CHAPTERS = 8;

function chapterAlternates(chapter: number): { languages: { es: string } } {
  return {
    languages: { es: `${SITE_URL}/es/?chapter=${chapter}` },
  };
}

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date();
  const entries: MetadataRoute.Sitemap = [
    {
      url: `${SITE_URL}/`,
      lastModified,
      changeFrequency: "weekly",
      priority: 1.0,
      alternates: { languages: { es: `${SITE_URL}/es/` } },
    },
    {
      url: `${SITE_URL}/assess`,
      lastModified,
      changeFrequency: "monthly",
      priority: 0.8,
      alternates: { languages: { es: `${SITE_URL}/es/assess` } },
    },
  ];

  for (let chapter = 1; chapter <= TOTAL_CHAPTERS; chapter += 1) {
    entries.push({
      url: `${SITE_URL}/?chapter=${chapter}`,
      lastModified,
      changeFrequency: "weekly",
      priority: 0.7,
      alternates: chapterAlternates(chapter),
    });
  }

  return entries;
}
