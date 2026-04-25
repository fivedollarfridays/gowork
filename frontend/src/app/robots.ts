/**
 * T13.117 — robots.txt (Next.js App Router convention).
 *
 * Next.js renders this module at request time as `/robots.txt`.
 *
 * Disallow rationale:
 *   - `/admin/`  — T13.8 QC dashboard; auth-gated, but we still don't want
 *     crawlers probing it (acceptance criterion for T13.117).
 *   - `/api/`    — frontend doesn't proxy backend routes, but defensive
 *     in case a future Next.js route handler is added there.
 *   - `/feedback/` — token-gated; tokens are unguessable secrets and
 *     pages also opt out via `robots: noindex` in their `generateMetadata`.
 *   - `/shared/`   — token-gated; same reasoning. T13.71 redacts PII
 *     from the share payload, but the URLs themselves shouldn't be
 *     indexed either.
 *
 * The site URL is read from `NEXT_PUBLIC_SITE_URL` (matches
 * `app/layout.tsx`'s default of `https://montgowork.com`).
 */
import type { MetadataRoute } from "next";

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://montgowork.com";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/admin/", "/api/", "/feedback/", "/shared/"],
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
