import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

/**
 * T2.1 — Mapbox token validation + static fallback chain.
 *
 * The W2 Wall lane needs a SINGLE choke point that decides whether to mount
 * Mapbox or fall back to the static Fort Worth screenshot. W1 shipped a sync
 * shape-check (`validateMapboxToken`); W2 layers a network probe on top so
 * we also catch CDN outages, malformed API responses, and slow networks.
 *
 * Three failure modes the static fallback must absorb:
 *   1. Token missing / blank
 *   2. Token malformed (not a public `pk.` token)
 *   3. Mapbox CDN unreachable (timeout, 5xx, fetch throw)
 *
 * Spotlight (Root Cause Lens): a hardened fallback chain prevents EVERY
 * downstream chapter from breaking when Mapbox has a bad day on demo day.
 */

describe("T2.1 — validateToken (sync shape-check)", () => {
  let envSnapshot: string | undefined;

  beforeEach(() => {
    envSnapshot = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
  });

  afterEach(() => {
    if (envSnapshot === undefined) {
      delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    } else {
      process.env.NEXT_PUBLIC_MAPBOX_TOKEN = envSnapshot;
    }
  });

  it("returns false when token missing", async () => {
    delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    const { validateToken } = await import("../mapboxToken");
    expect(validateToken()).toBe(false);
  });

  it("returns false when token is malformed (not pk.)", async () => {
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "sk.secret-keys-never-shipped";
    const { validateToken } = await import("../mapboxToken");
    expect(validateToken()).toBe(false);
  });

  it("returns true for a well-formed public token", async () => {
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "pk.eyJ1IjoiZ293b3JrIiwiYSI6ImNrIn0.signature";
    const { validateToken } = await import("../mapboxToken");
    expect(validateToken()).toBe(true);
  });
});

describe("T2.1 — isMapboxAvailable (async network probe)", () => {
  let envSnapshot: string | undefined;
  let fetchSpy: ReturnType<typeof vi.spyOn> | null = null;

  beforeEach(() => {
    envSnapshot = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    vi.useRealTimers();
  });

  afterEach(() => {
    if (envSnapshot === undefined) {
      delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    } else {
      process.env.NEXT_PUBLIC_MAPBOX_TOKEN = envSnapshot;
    }
    if (fetchSpy) {
      fetchSpy.mockRestore();
      fetchSpy = null;
    }
    vi.useRealTimers();
  });

  it("returns false when token missing (no fetch attempted)", async () => {
    delete process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    const fetchMock = vi.fn();
    fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation(fetchMock);

    const { isMapboxAvailable } = await import("../mapboxToken");
    const result = await isMapboxAvailable();

    expect(result).toBe(false);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("returns true when token valid AND CDN responds 200 OK", async () => {
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "pk.eyJ1IjoiZ293b3JrIiwiYSI6ImNrIn0.sig";
    fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200 }),
    );

    const { isMapboxAvailable } = await import("../mapboxToken");
    const result = await isMapboxAvailable();

    expect(result).toBe(true);
  });

  it("returns false when CDN responds 5xx (transient outage)", async () => {
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "pk.eyJ1IjoiZ293b3JrIiwiYSI6ImNrIn0.sig";
    fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("upstream gateway", { status: 502 }),
    );

    const { isMapboxAvailable } = await import("../mapboxToken");
    const result = await isMapboxAvailable();

    expect(result).toBe(false);
  });

  it("returns false (does not throw) when fetch rejects (network failure)", async () => {
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "pk.eyJ1IjoiZ293b3JrIiwiYSI6ImNrIn0.sig";
    fetchSpy = vi.spyOn(globalThis, "fetch").mockRejectedValue(
      new TypeError("Failed to fetch"),
    );

    const { isMapboxAvailable } = await import("../mapboxToken");
    const result = await isMapboxAvailable();

    expect(result).toBe(false);
  });

  it("returns false when fetch exceeds the 2s timeout", async () => {
    process.env.NEXT_PUBLIC_MAPBOX_TOKEN = "pk.eyJ1IjoiZ293b3JrIiwiYSI6ImNrIn0.sig";

    fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation((_input, init) => {
      // Honor AbortSignal — that's what the production timeout uses.
      return new Promise((_resolve, reject) => {
        const signal = (init as RequestInit | undefined)?.signal;
        signal?.addEventListener("abort", () => {
          reject(new DOMException("Aborted", "AbortError"));
        });
        // Otherwise hang forever — relies on the timeout firing.
      });
    });

    const { isMapboxAvailable } = await import("../mapboxToken");
    vi.useFakeTimers();

    const promise = isMapboxAvailable();
    // Drive past the 2s timeout.
    await vi.advanceTimersByTimeAsync(2_500);
    const result = await promise;

    expect(result).toBe(false);
  });
});
