import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    // Playwright owns the `e2e/` tree (T13.129). Vitest default-matches
    // `**/*.spec.ts`, which would otherwise try to load Playwright's
    // `test`/`expect` bindings inside jsdom and crash.
    exclude: ["**/node_modules/**", "**/dist/**", "**/.next/**", "e2e/**"],
    // W5 Driver D — T5.D.1: Raise the default test timeout from 5s to 10s.
    // Under full-suite parallel pressure (3675+ tests), `WallContainer*` and
    // `MapboxScene*` files occasionally tip over the 5s default because of
    // jsdom + Mapbox mock + Three.js mount cost. 10s is safely above the
    // pathological worst case (~2-3s observed) without masking real hangs.
    // Driver C confirmed `--no-file-parallelism` worked; this is the
    // least-invasive fix that keeps parallelism on.
    testTimeout: 10_000,
    hookTimeout: 10_000,
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
