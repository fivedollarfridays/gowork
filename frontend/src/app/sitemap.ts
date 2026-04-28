/**
 * T13.117 — Sitemap (Next.js App Router convention).
 *
 * Next.js renders this module at request time as `/sitemap.xml`.
 *
 * Route inventory rationale:
 *   - `/`, `/assess` are publicly discoverable hackathon-submission entry
 *     points and belong in the sitemap.
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

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://gowork.example";

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date();
  return [
    {
      url: `${SITE_URL}/`,
      lastModified,
      changeFrequency: "weekly",
      priority: 1.0,
    },
    {
      url: `${SITE_URL}/assess`,
      lastModified,
      changeFrequency: "monthly",
      priority: 0.8,
    },
  ];
}
