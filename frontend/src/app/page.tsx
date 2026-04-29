/**
 * Home page (server) — sprint/polish-2 Driver E (T51).
 *
 * The home route now ships per-chapter share cards. The server renders:
 *   - `generateMetadata({ searchParams })` reads `?chapter=N` (1..8) and
 *     emits an `og:image` pointing at `/api/og/[chapter]` so Twitter / X
 *     / LinkedIn / Slack unfurl a chapter-specific preview when a deep-
 *     link is shared.
 *   - A `<script type="application/ld+json">` tag with the WebSite +
 *     BreadcrumbList + (when chapter is set) Article schema, sourced
 *     from `lib/seo/structuredData.ts`.
 *   - The client island `HomeClient` (returning-user redirect + the
 *     `<HomePage>` chapter shell).
 *
 * The legacy hero/flow/stats landing remains preserved at `/archive`
 * for rollback insurance (T2.46).
 */
import type { Metadata } from "next";
import HomeClient from "./page-client";
import { buildHomeStructuredData } from "@/lib/seo/structuredData";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://gowork.example";

interface HomePageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

function readChapter(
  raw: string | string[] | undefined,
): number {
  if (Array.isArray(raw)) raw = raw[0];
  if (typeof raw !== "string") return 0;
  const n = Number.parseInt(raw, 10);
  if (Number.isNaN(n) || n < 1 || n > 8) return 0;
  return n;
}

function readLocale(
  raw: string | string[] | undefined,
): "en" | "es" {
  if (Array.isArray(raw)) raw = raw[0];
  return raw === "es" ? "es" : "en";
}

export async function generateMetadata(
  { searchParams }: HomePageProps,
): Promise<Metadata> {
  const sp = await searchParams;
  const chapter = readChapter(sp.chapter);
  const locale = readLocale(sp.locale);

  const ogPath = chapter >= 1 && chapter <= 8
    ? `/api/og/${chapter}?locale=${locale}`
    : `/api/og/default?locale=${locale}`;

  const canonicalPath = chapter >= 1 && chapter <= 8
    ? `/?chapter=${chapter}`
    : `/`;

  return {
    alternates: {
      canonical: `${SITE_URL}${canonicalPath}`,
      languages: {
        es: `${SITE_URL}/es${canonicalPath === "/" ? "/" : canonicalPath}`,
      },
    },
    openGraph: {
      url: `${SITE_URL}${canonicalPath}`,
      images: [
        {
          url: `${SITE_URL}${ogPath}`,
          width: 1200,
          height: 630,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      images: [`${SITE_URL}${ogPath}`],
    },
  };
}

export default async function Home({ searchParams }: HomePageProps) {
  const sp = await searchParams;
  const chapter = readChapter(sp.chapter);
  const locale = readLocale(sp.locale);
  const jsonld = buildHomeStructuredData({ chapter, locale });

  return (
    <>
      <script
        type="application/ld+json"
        // eslint-disable-next-line react/no-danger
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonld) }}
      />
      <HomeClient />
    </>
  );
}
