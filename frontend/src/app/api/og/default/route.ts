/**
 * T4.D.3 — Site-wide default OG card.
 *
 * GET /api/og/default?locale=en|es
 *
 * Returns a 1200×630 PNG with the site-level title + tagline. Used by
 * page metadata that doesn't have a chapter-specific URL fragment, and
 * as the canonical fallback when a chapter slug is invalid.
 */

import { ImageResponse } from "@vercel/og";
import {
  composeDefaultCard,
  CARD_HEIGHT,
  CARD_WIDTH,
} from "@/lib/og/cardComposer";

export const runtime = "edge";

function resolveLocale(url: URL): string {
  const raw = url.searchParams.get("locale") ?? "en";
  return raw === "es" ? "es" : "en";
}

export async function GET(req: Request) {
  const url = new URL(req.url);
  const locale = resolveLocale(url);
  const { tree } = composeDefaultCard(locale);

  return new ImageResponse(tree, {
    width: CARD_WIDTH,
    height: CARD_HEIGHT,
    headers: {
      "Cache-Control":
        "public, max-age=86400, stale-while-revalidate=604800",
    },
  });
}
