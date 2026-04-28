import { describe, it, expect } from "vitest";

/**
 * T2.58 — Mapbox lazy-load contract test.
 *
 * `WallContainer` MUST import `MapboxScene` via `next/dynamic` (not a
 * static import). Static imports would pull mapbox-gl (~600KB) into the
 * initial bundle and blow LCP on slow networks. The dynamic import is
 * the ssr:false escape hatch that keeps Mapbox out of the server render
 * AND out of the initial JS chunk.
 *
 * This test reads the file source and asserts the contract — a static
 * import of `./MapboxScene` would be caught immediately.
 */

describe("T2.58 — WallContainer lazy-loads MapboxScene", () => {
  it("uses next/dynamic, not a static import, for MapboxScene", async () => {
    const fs = await import("node:fs");
    const path = await import("node:path");
    const filePath = path.resolve(
      __dirname,
      "..",
      "WallContainer.tsx",
    );
    const source = fs.readFileSync(filePath, "utf-8");

    // Must import dynamic from next.
    expect(source).toMatch(/import\s+dynamic\s+from\s+["']next\/dynamic["']/);
    // Must call dynamic with the MapboxScene loader.
    expect(source).toMatch(/dynamic\s*\(\s*\(\s*\)\s*=>\s*import\s*\(\s*["']\.\/MapboxScene["']\s*\)/);
    // Must NOT have a top-level static import of MapboxScene (the loader
    // arrow is allowed but the static line would be).
    expect(source).not.toMatch(/^import\s+\w+\s+from\s+["']\.\/MapboxScene["']/m);
  });

  it("disables SSR for MapboxScene (mapbox-gl is browser-only)", async () => {
    const fs = await import("node:fs");
    const path = await import("node:path");
    const filePath = path.resolve(
      __dirname,
      "..",
      "WallContainer.tsx",
    );
    const source = fs.readFileSync(filePath, "utf-8");
    expect(source).toMatch(/ssr:\s*false/);
  });
});
