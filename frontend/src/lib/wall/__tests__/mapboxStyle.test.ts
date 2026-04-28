import { describe, it, expect, beforeEach, afterEach } from "vitest";

/**
 * T2.18 — Mapbox Studio custom style URL + fallback chain.
 *
 * The editorial dark Mapbox style is built in Mapbox Studio (manual,
 * one-time, ~30 min). The resulting style URL becomes a public env var:
 *
 *   NEXT_PUBLIC_MAPBOX_STYLE_URL=mapbox://styles/<account>/<style-id>
 *
 * If the env var is unset (Shawn hasn't built the Studio style yet, or a
 * preview deploy without the secret), `MapboxScene` falls back to the
 * stock dark style. This module is the single source of truth for that
 * resolution so chapters never duplicate the lookup.
 *
 * Spotlight (Honesty + Legacy Lens — Driver A): the runbook + JSON export
 * (T2.18 deliverable) gives us reproducibility even if the original Studio
 * account is lost. Code stays unchanged; only the env var swaps.
 */

describe("T2.18 — resolveMapboxStyleUrl", () => {
  let envSnapshot: string | undefined;

  beforeEach(() => {
    envSnapshot = process.env.NEXT_PUBLIC_MAPBOX_STYLE_URL;
  });

  afterEach(() => {
    if (envSnapshot === undefined) {
      delete process.env.NEXT_PUBLIC_MAPBOX_STYLE_URL;
    } else {
      process.env.NEXT_PUBLIC_MAPBOX_STYLE_URL = envSnapshot;
    }
  });

  it("returns the env-configured style URL when set", async () => {
    process.env.NEXT_PUBLIC_MAPBOX_STYLE_URL = "mapbox://styles/gowork/wall-dark-editorial-v1";
    const { resolveMapboxStyleUrl, FALLBACK_DARK_STYLE_URL } = await import("../mapboxStyle");
    const url = resolveMapboxStyleUrl();
    expect(url).toBe("mapbox://styles/gowork/wall-dark-editorial-v1");
    expect(url).not.toBe(FALLBACK_DARK_STYLE_URL);
  });

  it("falls back to mapbox dark-v11 when env var unset", async () => {
    delete process.env.NEXT_PUBLIC_MAPBOX_STYLE_URL;
    const { resolveMapboxStyleUrl, FALLBACK_DARK_STYLE_URL } = await import("../mapboxStyle");
    expect(resolveMapboxStyleUrl()).toBe(FALLBACK_DARK_STYLE_URL);
  });

  it("falls back when env var is blank/whitespace (treated as unset)", async () => {
    process.env.NEXT_PUBLIC_MAPBOX_STYLE_URL = "   ";
    const { resolveMapboxStyleUrl, FALLBACK_DARK_STYLE_URL } = await import("../mapboxStyle");
    expect(resolveMapboxStyleUrl()).toBe(FALLBACK_DARK_STYLE_URL);
  });

  it("rejects malformed style URLs (must start with mapbox://)", async () => {
    process.env.NEXT_PUBLIC_MAPBOX_STYLE_URL = "https://malicious.example/style.json";
    const { resolveMapboxStyleUrl, FALLBACK_DARK_STYLE_URL } = await import("../mapboxStyle");
    expect(resolveMapboxStyleUrl()).toBe(FALLBACK_DARK_STYLE_URL);
  });
});

describe("T2.18 — FALLBACK_DARK_STYLE_URL is the canonical Mapbox dark", () => {
  it("equals mapbox://styles/mapbox/dark-v11", async () => {
    const { FALLBACK_DARK_STYLE_URL } = await import("../mapboxStyle");
    expect(FALLBACK_DARK_STYLE_URL).toBe("mapbox://styles/mapbox/dark-v11");
  });
});

describe("T2.18 — light variant for /assess + /plan (W3 reuse)", () => {
  it("FALLBACK_LIGHT_STYLE_URL equals mapbox://styles/mapbox/light-v11", async () => {
    const { FALLBACK_LIGHT_STYLE_URL } = await import("../mapboxStyle");
    expect(FALLBACK_LIGHT_STYLE_URL).toBe("mapbox://styles/mapbox/light-v11");
  });
});
