import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright headless harness for MontGoWork frontend.
 *
 * Pairs with `.paircoder/qc/suites/*.qc.yaml` divona suites — Playwright
 * runs the `@critical` subset on every PR (T13.125), divona handles broad
 * interactive coverage. Source-of-truth contract documented in
 * `.paircoder/qc/suites/README.md`.
 *
 * To run locally:
 *   npm run test:e2e             # headless (CI-equivalent)
 *   npm run test:e2e:headed      # watch tests in a visible browser
 *   npm run test:e2e:debug       # step through tests in inspector
 *
 * Tag conventions:
 *   @critical — included in PR-gated CI run
 *   (untagged) — opt-in, run on demand
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 5_000 },

  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,

  reporter: [["line"], ["html", { open: "never" }]],

  use: {
    baseURL: process.env.STAGING_FRONTEND_URL || "http://localhost:3000",
    headless: true,
    viewport: { width: 1280, height: 720 },
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
