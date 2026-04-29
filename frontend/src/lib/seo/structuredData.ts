/**
 * structuredData.ts — polish-2 T51 / T52.
 *
 * JSON-LD generators for the GoWork home route + per-chapter deep links.
 * Output is consumed by `app/page.tsx generateMetadata` and inlined as a
 * `<script type="application/ld+json">` tag so Google + Bing crawlers can
 * surface chapter-specific share cards.
 *
 * Driver E owns the canonical implementation.
 */

export interface ChapterSeoMeta {
  /** 1..8 — chapter number for the deep-link query param. */
  chapter: number;
  /** Locale for the JSON-LD `inLanguage` field. */
  locale: "en" | "es";
}

/**
 * Build a `WebSite` + `BreadcrumbList` JSON-LD payload for the canonical
 * home route. Chapter-specific Article schema is layered on when `chapter`
 * is supplied (deep-link access via `?chapter=N`).
 */
export function buildHomeStructuredData(
  _meta: ChapterSeoMeta,
): Record<string, unknown>[] {
  // SCAFFOLD — Driver E fills.
  return [];
}
