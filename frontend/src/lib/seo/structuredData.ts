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

const SCHEMA_CONTEXT = "https://schema.org";
const SITE_NAME = "GoWork";
const SITE_TAGLINE = "Workforce infrastructure for any American city.";

function siteUrl(): string {
  return process.env.NEXT_PUBLIC_SITE_URL ?? "https://gowork.example";
}

export type SeoLocale = "en" | "es";

export interface ChapterSeoMeta {
  /** 1..8 — chapter number for the deep-link query param. 0 / out-of-range → home only. */
  chapter: number;
  /** Locale for the JSON-LD `inLanguage` field. */
  locale: SeoLocale;
}

interface ChapterCopy {
  readonly headline: { readonly en: string; readonly es: string };
  readonly description: { readonly en: string; readonly es: string };
}

const CHAPTER_COPY: Record<number, ChapterCopy> = {
  1: {
    headline: { en: "The Wall", es: "El muro" },
    description: {
      en: "What's standing between you and a job?",
      es: "¿Qué se interpone entre tú y un empleo?",
    },
  },
  2: {
    headline: { en: "The Numbers", es: "Los números" },
    description: {
      en: "The cost of the wall, by the numbers.",
      es: "El costo del muro, en cifras.",
    },
  },
  3: {
    headline: { en: "Meet Carlos", es: "Conoce a Carlos" },
    description: {
      en: "A worker in Fort Worth — seven barriers, one path.",
      es: "Un trabajador en Fort Worth — siete barreras, un camino.",
    },
  },
  4: {
    headline: { en: "The Map", es: "El mapa" },
    description: {
      en: "Fort Worth, mapped — employers, transit, time.",
      es: "Fort Worth, mapeado — empleadores, transporte, tiempo.",
    },
  },
  5: {
    headline: { en: "The Plan", es: "El plan" },
    description: {
      en: "Sequenced steps — the math, the order, the hand-off.",
      es: "Pasos secuenciados — las cuentas, el orden, la entrega.",
    },
  },
  6: {
    headline: { en: "Live Jobs", es: "Empleos en vivo" },
    description: {
      en: "Open roles in Fort Worth, this week.",
      es: "Vacantes en Fort Worth, esta semana.",
    },
  },
  7: {
    headline: { en: "The Cliff", es: "El precipicio" },
    description: {
      en: "The wage cliff, and the path across it.",
      es: "El precipicio salarial y cómo cruzarlo.",
    },
  },
  8: {
    headline: { en: "Find Your Path", es: "Encuentra tu camino" },
    description: {
      en: "Start your assessment.",
      es: "Comienza tu evaluación.",
    },
  },
};

function isValidChapter(chapter: number): boolean {
  return Number.isInteger(chapter) && chapter >= 1 && chapter <= 8;
}

function buildWebSite(locale: SeoLocale): Record<string, unknown> {
  return {
    "@context": SCHEMA_CONTEXT,
    "@type": "WebSite",
    name: SITE_NAME,
    description: SITE_TAGLINE,
    url: siteUrl(),
    inLanguage: locale,
  };
}

function buildBreadcrumbs(
  locale: SeoLocale,
  chapter: number,
): Record<string, unknown> {
  const home = locale === "es" ? "Inicio" : "Home";
  const list: Array<Record<string, unknown>> = [
    {
      "@type": "ListItem",
      position: 1,
      name: home,
      item: `${siteUrl()}/`,
    },
  ];
  if (isValidChapter(chapter)) {
    const copy = CHAPTER_COPY[chapter];
    const label = locale === "es" ? "Capítulo" : "Chapter";
    list.push({
      "@type": "ListItem",
      position: 2,
      name: `${label} ${chapter} — ${copy.headline[locale]}`,
      item: `${siteUrl()}/?chapter=${chapter}`,
    });
  }
  return {
    "@context": SCHEMA_CONTEXT,
    "@type": "BreadcrumbList",
    itemListElement: list,
  };
}

function buildArticle(
  locale: SeoLocale,
  chapter: number,
): Record<string, unknown> | null {
  if (!isValidChapter(chapter)) return null;
  const copy = CHAPTER_COPY[chapter];
  return {
    "@context": SCHEMA_CONTEXT,
    "@type": "Article",
    headline: copy.headline[locale],
    description: copy.description[locale],
    inLanguage: locale,
    url: `${siteUrl()}/?chapter=${chapter}`,
    image: `${siteUrl()}/api/og/${chapter}?locale=${locale}`,
    publisher: {
      "@type": "Organization",
      name: SITE_NAME,
      url: siteUrl(),
    },
  };
}

/**
 * Build a `WebSite` + `BreadcrumbList` JSON-LD payload for the canonical
 * home route. Chapter-specific Article schema is layered on when `chapter`
 * is in the 1..8 range (deep-link access via `?chapter=N`).
 */
export function buildHomeStructuredData(
  meta: ChapterSeoMeta,
): Record<string, unknown>[] {
  const out: Record<string, unknown>[] = [
    buildWebSite(meta.locale),
    buildBreadcrumbs(meta.locale, meta.chapter),
  ];
  const article = buildArticle(meta.locale, meta.chapter);
  if (article) out.push(article);
  return out;
}
