import { test, expect } from "@playwright/test";

/**
 * Worker-onboarding critical path.
 *
 * Mirrors the divona `worker-onboarding.qc.yaml` suite (authored under
 * T13.10) — same demo session, same assertions, same expected outcomes.
 * Until the .qc.yaml lands, this Playwright spec is the de facto reference.
 *
 * Tagged `@critical` so the T13.125 PR-gating CI workflow can filter to
 * the top-five paths via `playwright test --grep "@critical"`.
 *
 * Runs against `localhost:3000` (the dev server is started by
 * `playwright.config.ts.webServer`). No production data is seeded —
 * the home page does not require auth, so the demo flow exercises the
 * public marketing-into-assess transition without DB mutation.
 */
test.describe("@critical worker onboarding", () => {
  test("home page renders the value-prop hero and CTAs", async ({ page }) => {
    await page.goto("/");

    // Hero headline is animated word-by-word via Typewriter; assert the
    // h1 element exists and contains the trailing question word once
    // animation settles.
    const heading = page.getByRole("heading", { level: 1 });
    await expect(heading).toBeVisible();
    await expect(heading).toContainText(/job/i);

    // The "How It Works" section enumerates the three onboarding steps.
    await expect(
      page.getByRole("heading", { name: /how it works/i }),
    ).toBeVisible();
    await expect(page.getByRole("heading", { name: /^Assess$/ })).toBeVisible();
    await expect(page.getByRole("heading", { name: /^Match$/ })).toBeVisible();
    await expect(page.getByRole("heading", { name: /^Plan$/ })).toBeVisible();

    // Primary CTA into the assess flow.
    await expect(
      page.getByRole("link", { name: /get your plan/i }).first(),
    ).toBeVisible();
  });

  test("CTA link navigates to the assess wizard", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: /get your plan/i }).first().click();

    await page.waitForURL("**/assess");
    expect(page.url()).toContain("/assess");

    // The assess wizard renders an h1 (assessment title).
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

    // Step 1 ("Basic Info") shows ZIP + Employment fields.
    await expect(page.getByLabel(/ZIP Code/i)).toBeVisible();
    await expect(page.getByLabel(/Employment Status/i)).toBeVisible();

    // Wizard chrome: the advance button on step 1 is labelled
    // "Go to step 2: Resume" via aria-label (WizardShell.tsx).
    await expect(
      page.getByRole("button", { name: /Go to step 2/i }),
    ).toBeVisible();
  });

  test("home page logs no console errors during initial render", async ({
    page,
  }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        errors.push(msg.text());
      }
    });
    page.on("pageerror", (err) => {
      errors.push(err.message);
    });

    await page.goto("/");
    // Allow client-side hydration + animation to settle.
    await page.waitForLoadState("networkidle");

    // Filter known-benign noise from the dev server. The goal is to
    // catch *application* errors thrown from React/page code, not
    // infrastructure quirks of the local Next.js dev process:
    //   - Failed-to-load resource warnings (404 favicon, etc.)
    //   - HMR socket pings during hot reload
    //   - React-DevTools install hint
    //   - CSP `connect-src` denials when localhost:8000 is unset
    //   - MIME-type "Refused to execute" warnings from a stale .next/
    //     cache (refresh by deleting frontend/.next)
    const benign = [
      /Failed to load resource/,
      /HMR/i,
      /Download the React DevTools/,
      /Content Security Policy/i,
      /Refused to connect/i,
      /Refused to execute script/i,
      /Refused to apply style/i,
      /strict MIME/i,
      // Backend at localhost:8000 may not be running for a frontend-only
      // smoke test; CORS rejection is infra noise, not an app error.
      /CORS policy/i,
      /blocked by CORS/i,
    ];
    const fatal = errors.filter(
      (e) => !benign.some((pattern) => pattern.test(e)),
    );
    expect(fatal).toEqual([]);
  });
});
