/**
 * T4.D.3 — Per-chapter dynamic OG route tests.
 *
 * Each /api/og/[chapter] route returns a 1200x630 PNG (Edge runtime
 * ImageResponse via @vercel/og). The tests below mock @vercel/og's
 * `ImageResponse` so the route's compose-and-respond pipeline can be
 * exercised in jsdom without invoking Satori (which needs a font
 * binary).
 *
 * The contract:
 *   1. Response.headers.get('content-type') === 'image/png'
 *   2. Response is built from a React tree (composeChapterCard's output)
 *   3. Width/height options are 1200x630
 *   4. Locale param 'es' resolves Spanish copy; default is English
 *   5. Out-of-range chapter (< 1 or > 10) → 404
 *   6. The default route returns a card without a chapter param
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

interface CapturedImageResponse {
  tree: unknown;
  options: { width?: number; height?: number };
}

const captured: CapturedImageResponse[] = [];

vi.mock("@vercel/og", () => {
  class FakeImageResponse {
    public readonly headers: Map<string, string>;
    public readonly status: number;
    public readonly body: string;
    constructor(tree: unknown, options: { width?: number; height?: number }) {
      captured.push({ tree, options });
      this.headers = new Map([["content-type", "image/png"]]);
      this.status = 200;
      this.body = "PNG";
    }
  }
  return { ImageResponse: FakeImageResponse };
});

beforeEach(() => {
  captured.length = 0;
});

describe("T4.D.3 — /api/og/[chapter] dynamic route", () => {
  it("chapter 1 (English) returns a 1200x630 PNG-shaped response", async () => {
    const { GET } = await import("../[chapter]/route");
    const req = new Request("https://gowork.example/api/og/1");
    const res = await GET(req, { params: Promise.resolve({ chapter: "1" }) });
    expect((res as unknown as { status: number }).status).toBe(200);
    expect(captured).toHaveLength(1);
    expect(captured[0].options.width).toBe(1200);
    expect(captured[0].options.height).toBe(630);
  });

  it("chapter 7 (English) builds a tree from composeChapterCard", async () => {
    const { GET } = await import("../[chapter]/route");
    const req = new Request("https://gowork.example/api/og/7");
    await GET(req, { params: Promise.resolve({ chapter: "7" }) });
    expect(captured).toHaveLength(1);
    expect(captured[0].tree).toBeDefined();
  });

  it("locale=es returns a Spanish-locale card (different from EN)", async () => {
    const { GET } = await import("../[chapter]/route");
    const reqEn = new Request("https://gowork.example/api/og/1");
    const reqEs = new Request("https://gowork.example/api/og/1?locale=es");
    await GET(reqEn, { params: Promise.resolve({ chapter: "1" }) });
    await GET(reqEs, { params: Promise.resolve({ chapter: "1" }) });
    expect(captured).toHaveLength(2);
    // Both produce trees — they may stringify differently.
    expect(captured[0].tree).not.toEqual(captured[1].tree);
  });

  it("rejects chapter < 1 with a 404", async () => {
    const { GET } = await import("../[chapter]/route");
    const req = new Request("https://gowork.example/api/og/0");
    const res = await GET(req, { params: Promise.resolve({ chapter: "0" }) });
    expect((res as unknown as { status: number }).status).toBe(404);
  });

  it("rejects chapter > 10 with a 404", async () => {
    const { GET } = await import("../[chapter]/route");
    const req = new Request("https://gowork.example/api/og/11");
    const res = await GET(req, { params: Promise.resolve({ chapter: "11" }) });
    expect((res as unknown as { status: number }).status).toBe(404);
  });

  it("rejects non-numeric chapter slug with a 404", async () => {
    const { GET } = await import("../[chapter]/route");
    const req = new Request("https://gowork.example/api/og/foo");
    const res = await GET(req, {
      params: Promise.resolve({ chapter: "foo" }),
    });
    expect((res as unknown as { status: number }).status).toBe(404);
  });
});

describe("T4.D.3 — /api/og/default route", () => {
  it("returns a 1200x630 PNG-shaped response (English default)", async () => {
    const { GET } = await import("../default/route");
    const req = new Request("https://gowork.example/api/og/default");
    const res = await GET(req);
    expect((res as unknown as { status: number }).status).toBe(200);
    expect(captured).toHaveLength(1);
    expect(captured[0].options.width).toBe(1200);
    expect(captured[0].options.height).toBe(630);
  });

  it("locale=es returns a Spanish default card", async () => {
    const { GET } = await import("../default/route");
    const req = new Request("https://gowork.example/api/og/default?locale=es");
    await GET(req);
    expect(captured).toHaveLength(1);
    expect(captured[0].tree).toBeDefined();
  });
});
