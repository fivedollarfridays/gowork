/**
 * T5.B.5 — /api/og/[chapter] static fallback behavior test.
 *
 * Mocks @vercel/og to throw, then verifies the route returns a 307
 * redirect to /og/<chapter>.png. This guards the rescue path that
 * keeps the demo unfurl-able when Satori errors live.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

// Spy capture for any successful ImageResponse construction.
const successCalls: number[] = [];

vi.mock("@vercel/og", () => {
  class ThrowingImageResponse {
    constructor() {
      successCalls.push(1);
      throw new Error("Simulated Satori failure (font binary missing)");
    }
  }
  return { ImageResponse: ThrowingImageResponse };
});

beforeEach(() => {
  successCalls.length = 0;
  // Silence the route's diagnostic console.error — we expect it to fire
  // for the simulated-Satori-failure tests, that's the whole point.
  vi.spyOn(console, "error").mockImplementation(() => undefined);
});

interface RedirectShape {
  status: number;
  headers: { get: (k: string) => string | null };
}

describe("T5.B.5 — /api/og/[chapter] Satori-error fallback", () => {
  it("redirects 307 to /og/<chapter>.png when ImageResponse throws", async () => {
    const { GET } = await import("../[chapter]/route");
    const req = new Request("https://gowork.example/api/og/4");
    const res = (await GET(req, {
      params: Promise.resolve({ chapter: "4" }),
    })) as unknown as RedirectShape;

    // Response.redirect returns a 307 with a Location header by default.
    expect([301, 302, 307, 308]).toContain(res.status);
    const location = res.headers.get("location");
    expect(location).toBeTruthy();
    expect(location).toMatch(/\/og\/4\.png$/);
  });

  it("preserves the request origin in the fallback URL", async () => {
    const { GET } = await import("../[chapter]/route");
    const req = new Request("https://example.test/api/og/9");
    const res = (await GET(req, {
      params: Promise.resolve({ chapter: "9" }),
    })) as unknown as RedirectShape;
    const location = res.headers.get("location");
    expect(location).toMatch(/^https:\/\/example\.test\/og\/9\.png$/);
  });

  it("still 404s on out-of-range chapter (Satori never invoked)", async () => {
    const { GET } = await import("../[chapter]/route");
    const req = new Request("https://gowork.example/api/og/99");
    const res = (await GET(req, {
      params: Promise.resolve({ chapter: "99" }),
    })) as unknown as RedirectShape;
    expect(res.status).toBe(404);
    // ImageResponse must NOT have been attempted for invalid chapters.
    expect(successCalls.length).toBe(0);
  });
});
