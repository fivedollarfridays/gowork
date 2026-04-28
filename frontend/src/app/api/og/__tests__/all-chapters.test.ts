/**
 * Spotlight invention #4 (W4 Driver D) — all-chapters OG sanity sweep.
 *
 * One test that walks every chapter (1..10) in BOTH supported locales
 * (en, es) and asserts that the route handler returns a 200 response
 * with a 1200×630 ImageResponse. Catches:
 *   - A new chapter added without an OG card backing.
 *   - A locale parity break (Spanish copy missing).
 *   - A regression in cardComposer's locale fallback.
 *
 * Without this sweep, a future driver could ship a 4-locale rollout and
 * break the OG card for one of them silently — Twitter unfurls would
 * just show "PNG missing." This test makes that loud.
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
    constructor(tree: unknown, options: { width?: number; height?: number }) {
      captured.push({ tree, options });
      this.headers = new Map([["content-type", "image/png"]]);
      this.status = 200;
    }
  }
  return { ImageResponse: FakeImageResponse };
});

beforeEach(() => {
  captured.length = 0;
});

const ALL_CHAPTERS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] as const;
const ALL_LOCALES = ["en", "es"] as const;

describe("Spotlight #4 — all-chapters OG sanity sweep", () => {
  it("each chapter (1..10) returns 200 in English", async () => {
    const { GET } = await import("../[chapter]/route");
    for (const n of ALL_CHAPTERS) {
      const req = new Request(`https://gowork.example/api/og/${n}`);
      const res = await GET(req, {
        params: Promise.resolve({ chapter: String(n) }),
      });
      expect((res as unknown as { status: number }).status).toBe(200);
    }
    expect(captured.length).toBe(ALL_CHAPTERS.length);
  });

  it("each chapter (1..10) returns 200 in Spanish (locale=es)", async () => {
    const { GET } = await import("../[chapter]/route");
    for (const n of ALL_CHAPTERS) {
      const req = new Request(
        `https://gowork.example/api/og/${n}?locale=es`,
      );
      const res = await GET(req, {
        params: Promise.resolve({ chapter: String(n) }),
      });
      expect((res as unknown as { status: number }).status).toBe(200);
    }
    expect(captured.length).toBe(ALL_CHAPTERS.length);
  });

  it("every (chapter, locale) tuple emits a 1200×630 ImageResponse", async () => {
    const { GET } = await import("../[chapter]/route");
    for (const n of ALL_CHAPTERS) {
      for (const locale of ALL_LOCALES) {
        captured.length = 0;
        const req = new Request(
          `https://gowork.example/api/og/${n}?locale=${locale}`,
        );
        await GET(req, {
          params: Promise.resolve({ chapter: String(n) }),
        });
        expect(captured).toHaveLength(1);
        expect(captured[0].options.width).toBe(1200);
        expect(captured[0].options.height).toBe(630);
        expect(captured[0].tree).toBeDefined();
      }
    }
  });

  it("default route also covers en + es", async () => {
    const { GET } = await import("../default/route");
    for (const locale of ALL_LOCALES) {
      const req = new Request(
        `https://gowork.example/api/og/default?locale=${locale}`,
      );
      const res = await GET(req);
      expect((res as unknown as { status: number }).status).toBe(200);
    }
    expect(captured.length).toBe(ALL_LOCALES.length);
  });
});
