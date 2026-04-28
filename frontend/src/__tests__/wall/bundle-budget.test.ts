import { describe, it, expect } from "vitest";

/**
 * T2.66 + T2.58 — Bundle budget contract.
 *
 * The W2 lazy-load contract: mapbox-gl (~600KB) MUST stay out of the
 * initial JavaScript bundle. The dynamic import in WallContainer
 * achieves this; this test pins a budget so a regression (e.g., someone
 * accidentally promotes mapbox-gl to a static import) breaks loudly.
 *
 * The actual bundle inspection lives in `frontend/scripts/bundle-size-check.mjs`
 * (run via `npm run size:check`); this vitest is a static contract guard
 * verifying the source files don't smuggle in mapbox-gl statically.
 *
 * As of W2 close (post-build smoke):
 *   /          → 115 kB First Load JS (Mapbox lazy)
 *   /archive   → 163 kB First Load JS (legacy bundle)
 *   shared     → 102 kB
 */

describe("T2.66 — bundle contract: mapbox-gl stays out of static imports", () => {
  it("page.tsx does NOT statically import mapbox-gl or react-map-gl", async () => {
    const fs = await import("node:fs");
    const path = await import("node:path");
    const filePath = path.resolve(__dirname, "..", "..", "app", "page.tsx");
    const source = fs.readFileSync(filePath, "utf-8");
    expect(source).not.toMatch(/from\s+["']mapbox-gl["']/);
    expect(source).not.toMatch(/from\s+["']react-map-gl["']/);
  });

  it("WallContainer.tsx does NOT statically import mapbox-gl", async () => {
    const fs = await import("node:fs");
    const path = await import("node:path");
    const filePath = path.resolve(
      __dirname,
      "..",
      "..",
      "components",
      "wall",
      "WallContainer.tsx",
    );
    const source = fs.readFileSync(filePath, "utf-8");
    // WallContainer does not consume mapbox-gl directly — that's
    // MapboxScene's job, and MapboxScene is dynamic-imported.
    expect(source).not.toMatch(/from\s+["']mapbox-gl["']/);
    expect(source).not.toMatch(/from\s+["']react-map-gl["']/);
  });

  it("MapboxScene.tsx is the ONLY component importing react-map-gl", async () => {
    // This is a soft-check — guards against future drift. If chapters
    // start importing react-map-gl directly, lazy-load benefit is lost.
    const fs = await import("node:fs");
    const path = await import("node:path");
    const wallDir = path.resolve(__dirname, "..", "..", "components", "wall");
    const entries = fs.readdirSync(wallDir);

    const offenders: string[] = [];
    for (const entry of entries) {
      const fullPath = path.join(wallDir, entry);
      if (!fs.statSync(fullPath).isFile()) continue;
      if (entry === "MapboxScene.tsx") continue;
      if (!entry.endsWith(".tsx")) continue;
      const source = fs.readFileSync(fullPath, "utf-8");
      if (/from\s+["']react-map-gl["']/.test(source)) {
        offenders.push(entry);
      }
    }
    expect(offenders).toEqual([]);
  });
});
