/**
 * polish-2 T51 — page.tsx generateMetadata + JSON-LD tests.
 *
 * Verifies the server `generateMetadata` reads `searchParams.chapter`
 * and emits per-chapter `og:image` pointing at `/api/og/[chapter]`,
 * and that the canonical link is set.
 */
import { describe, it, expect } from "vitest";
import { generateMetadata } from "../page";

interface SearchParamsLike {
  chapter?: string | string[];
  locale?: string | string[];
}

async function callMeta(searchParams: SearchParamsLike) {
  return generateMetadata({
    searchParams: Promise.resolve(searchParams),
  } as Parameters<typeof generateMetadata>[0]);
}

describe("generateMetadata (polish-2 T51)", () => {
  it("returns metadata with og:image pointing at /api/og/3 when ?chapter=3", async () => {
    const meta = await callMeta({ chapter: "3" });
    const ogImages = (meta.openGraph?.images ?? []) as Array<{ url: string }>;
    const url = String(ogImages[0]?.url ?? "");
    expect(url).toMatch(/\/api\/og\/3/);
  });

  it("returns metadata with og:image /api/og/4 when ?chapter=4", async () => {
    const meta = await callMeta({ chapter: "4" });
    const ogImages = (meta.openGraph?.images ?? []) as Array<{ url: string }>;
    const url = String(ogImages[0]?.url ?? "");
    expect(url).toMatch(/\/api\/og\/4/);
  });

  it("falls back to /api/og/default when no chapter is supplied", async () => {
    const meta = await callMeta({});
    const ogImages = (meta.openGraph?.images ?? []) as Array<{ url: string }>;
    const url = String(ogImages[0]?.url ?? "");
    expect(url).toMatch(/\/api\/og\/default/);
  });

  it("ignores out-of-range chapter and falls back to default OG", async () => {
    const meta = await callMeta({ chapter: "99" });
    const ogImages = (meta.openGraph?.images ?? []) as Array<{ url: string }>;
    const url = String(ogImages[0]?.url ?? "");
    expect(url).toMatch(/\/api\/og\/default/);
  });

  it("declares a canonical link on the home route", async () => {
    const meta = await callMeta({});
    expect(meta.alternates?.canonical).toBeDefined();
  });

  it("the canonical URL points at the home root with the chapter query when set", async () => {
    const meta = await callMeta({ chapter: "5" });
    expect(String(meta.alternates?.canonical)).toMatch(/\?chapter=5$/);
  });
});
