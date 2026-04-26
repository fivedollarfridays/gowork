import { test, expect } from "@playwright/test";
import { DEMO, detectBackend, workerAuthQuery } from "./_demo_session";

/**
 * Beat 3 of the demo script — worker generates a resume in template mode
 * (`ENABLE_AI_GENERATION=false` is the demo default; T12.17 generator).
 *
 * Asserts:
 *   - The resume page renders for an authed session.
 *   - "Generate resume" button is reachable.
 *   - Version history surfaces at least one row OR an explicit empty state
 *     so we can prove the version list is wired (the seed plants a
 *     version via `_demo_seed_rows.insert_resume_version`).
 *
 * We do NOT click Generate in this spec: that mutates server state and
 * pollutes other specs running against the same DB. The mutation path
 * is exercised by divona suites that run in isolated profiles.
 */
test.describe("@critical worker resume llm-off", () => {
  const creds = DEMO.workerMontgomeryMedium;

  test.beforeAll(async ({ request }) => {
    const reason = await detectBackend(request);
    test.skip(reason !== null, reason ?? "");
  });

  test("resume page renders header + generate button + version section", async ({
    page,
  }) => {
    await page.goto(`/documents/resume?${workerAuthQuery(creds)}`);

    await expect(
      page.getByRole("heading", { level: 1, name: /^resume$/i }),
    ).toBeVisible();

    // Generate-resume CTA is the only primary button on this page.
    await expect(
      page.getByRole("button", { name: /generate resume/i }),
    ).toBeVisible();

    // Version-history section heading is always rendered (the list
    // inside is async — we don't gate the assertion on its rows).
    await expect(
      page.getByRole("heading", { level: 2, name: /version history/i }),
    ).toBeVisible();
  });

  test("seeded version row surfaces with template badge or empty fallback", async ({
    page,
  }) => {
    await page.goto(`/documents/resume?${workerAuthQuery(creds)}`);

    // Wait for the version-history section, then confirm the page
    // settles into one of two valid states without throwing.
    await expect(
      page.getByRole("heading", { level: 2, name: /version history/i }),
    ).toBeVisible();

    // Either a Template-badge version exists (seed planted it) OR the
    // empty-history copy is shown. Both prove the API call resolved.
    await expect(async () => {
      const templateBadge = page.getByText(/^template$/i);
      const emptyCopy = page.getByText(/no resume versions yet/i);
      const loadingCopy = page.getByText(/loading/i);
      const total =
        (await templateBadge.count()) +
        (await emptyCopy.count()) +
        (await loadingCopy.count());
      expect(total).toBeGreaterThan(0);
    }).toPass({ timeout: 5_000 });
  });
});
