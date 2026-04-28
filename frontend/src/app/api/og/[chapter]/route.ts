/**
 * T4.D.3 — Per-chapter dynamic OG card route.
 *
 * GET /api/og/[chapter]?locale=en|es
 *
 * Returns a 1200×630 PNG composed by `composeChapterCard(chapter, locale)`
 * and rendered via @vercel/og's `ImageResponse` (Edge runtime, Satori
 * under the hood).
 *
 * # Why per-chapter
 *
 * Twitter / X / LinkedIn / Slack unfurl different OG images for different
 * URL fragments (#chapter-7 vs #chapter-1). Each Wall chapter gets its
 * own card so the share preview matches the chapter the link points at.
 *
 * # Locale
 *
 * `?locale=es` returns Spanish copy (Driver B's parity sweep applies).
 * Anything else falls back to English. We never crash on an unknown
 * locale — judges scouting on a /?locale=fr URL still get a card.
 *
 * # Caching
 *
 * `Cache-Control: public, max-age=86400, stale-while-revalidate=604800`
 * — content is deterministic for (chapter, locale) so a 1-day fresh
 * window with a 7-day grace works for press-kit scout traffic.
 */

import { ImageResponse } from "@vercel/og";
import {
  composeChapterCard,
  CARD_HEIGHT,
  CARD_WIDTH,
  type ChapterNumber,
} from "@/lib/og/cardComposer";

export const runtime = "edge";

interface RouteContext {
  params: Promise<{ chapter: string }>;
}

const VALID_CHAPTER_SET = new Set<number>([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);

function parseChapter(slug: string): ChapterNumber | null {
  const n = Number.parseInt(slug, 10);
  if (!Number.isFinite(n)) return null;
  if (!VALID_CHAPTER_SET.has(n)) return null;
  return n as ChapterNumber;
}

function resolveLocale(url: URL): string {
  const raw = url.searchParams.get("locale") ?? "en";
  return raw === "es" ? "es" : "en";
}

export async function GET(req: Request, context: RouteContext) {
  const { chapter: slug } = await context.params;
  const chapter = parseChapter(slug);
  if (chapter === null) {
    return new Response("Not Found", { status: 404 });
  }

  const url = new URL(req.url);
  const locale = resolveLocale(url);
  const { tree } = composeChapterCard(chapter, locale);

  return new ImageResponse(tree, {
    width: CARD_WIDTH,
    height: CARD_HEIGHT,
    headers: {
      "Cache-Control":
        "public, max-age=86400, stale-while-revalidate=604800",
    },
  });
}
