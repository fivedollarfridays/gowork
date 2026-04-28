/**
 * /api/og/[chapter] route headers contract.
 *
 * Pinned headers:
 *   - Cache-Control with public, max-age, stale-while-revalidate
 *   - Edge runtime export (`runtime = 'edge'`)
 *   - 404 for invalid chapter slugs is `text/plain` (Next default)
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

interface Captured {
  options: { width?: number; height?: number; headers?: Record<string, string> };
  tree: unknown;
}

const captured: Captured[] = [];

vi.mock("@vercel/og", () => {
  class FakeImageResponse {
    public readonly headers: Map<string, string>;
    public readonly status: number;
    constructor(
      tree: unknown,
      options: {
        width?: number;
        height?: number;
        headers?: Record<string, string>;
      },
    ) {
      captured.push({ tree, options });
      const hdrs = new Map<string, string>([["content-type", "image/png"]]);
      if (options?.headers) {
        for (const [k, v] of Object.entries(options.headers)) {
          hdrs.set(k.toLowerCase(), v);
        }
      }
      this.headers = hdrs;
      this.status = 200;
    }
  }
  return { ImageResponse: FakeImageResponse };
});

beforeEach(() => {
  captured.length = 0;
});

describe("OG route headers — caching", () => {
  it("chapter route sets Cache-Control with public + max-age", async () => {
    const { GET } = await import("../[chapter]/route");
    const req = new Request("https://gowork.example/api/og/1");
    await GET(req, { params: Promise.resolve({ chapter: "1" }) });
    expect(captured[0].options.headers?.["Cache-Control"]).toMatch(
      /public.*max-age/,
    );
  });

  it("chapter route Cache-Control includes stale-while-revalidate", async () => {
    const { GET } = await import("../[chapter]/route");
    const req = new Request("https://gowork.example/api/og/2");
    await GET(req, { params: Promise.resolve({ chapter: "2" }) });
    expect(captured[0].options.headers?.["Cache-Control"]).toMatch(
      /stale-while-revalidate/,
    );
  });

  it("default route also sets Cache-Control", async () => {
    const { GET } = await import("../default/route");
    const req = new Request("https://gowork.example/api/og/default");
    await GET(req);
    expect(captured[0].options.headers?.["Cache-Control"]).toMatch(
      /public.*max-age/,
    );
  });
});

describe("OG route runtime export", () => {
  it("chapter route exports runtime = 'edge'", async () => {
    const mod = await import("../[chapter]/route");
    expect((mod as unknown as { runtime: string }).runtime).toBe("edge");
  });

  it("default route exports runtime = 'edge'", async () => {
    const mod = await import("../default/route");
    expect((mod as unknown as { runtime: string }).runtime).toBe("edge");
  });
});

describe("OG route 404 path", () => {
  it("invalid chapter (chapter='abc') returns 404 plain", async () => {
    const { GET } = await import("../[chapter]/route");
    const req = new Request("https://gowork.example/api/og/abc");
    const res = await GET(req, { params: Promise.resolve({ chapter: "abc" }) });
    expect((res as unknown as { status: number }).status).toBe(404);
  });

  it("chapter=11 (out of range) returns 404", async () => {
    const { GET } = await import("../[chapter]/route");
    const req = new Request("https://gowork.example/api/og/11");
    const res = await GET(req, { params: Promise.resolve({ chapter: "11" }) });
    expect((res as unknown as { status: number }).status).toBe(404);
  });

  it("chapter=-1 returns 404", async () => {
    const { GET } = await import("../[chapter]/route");
    const req = new Request("https://gowork.example/api/og/-1");
    const res = await GET(req, { params: Promise.resolve({ chapter: "-1" }) });
    expect((res as unknown as { status: number }).status).toBe(404);
  });
});
