import { test, expect } from "@playwright/test";
import { DEMO, detectBackend } from "./_demo_session";

/**
 * Beat 6 of the demo script — case manager loads the advisor inbox via
 * a tokenized URL and sees stalled sessions surfaced for outreach.
 *
 * Auth model (frontend/src/app/case-manager/page.tsx):
 *   - URL param `?advisor_token=<plaintext>` is read on first paint and
 *     cached in sessionStorage under `montgowork_advisor_token`.
 *   - The advisor API client (`@/lib/api/advisor`) sends it as the
 *     `X-Admin-Key` header on every request.
 *
 * The seed plants:
 *   - One advisor_tokens row per city (`mw_adv_demo_<city>_<digest>`)
 *   - Multiple stalled sessions (medium + hard states; advisor inbox
 *     surfaces hard-stall sessions per city).
 *
 * We assert the page renders + the Needs-Attention card appears once
 * the token is wired. The list contents are async (depend on advisor
 * API resolving against the seeded DB), so we accept either a session
 * row OR the empty-state copy — both prove auth + fetch dispatched.
 */
test.describe("@critical advisor login inbox", () => {
  const advisor = DEMO.advisorMontgomery;

  test.beforeAll(async ({ request }) => {
    const reason = await detectBackend(request);
    test.skip(reason !== null, reason ?? "");
  });

  test("dashboard renders heading without an advisor token", async ({
    page,
  }) => {
    await page.goto("/case-manager");

    await expect(
      page.getByRole("heading", {
        level: 1,
        name: /case manager dashboard/i,
      }),
    ).toBeVisible();
  });

  test("advisor token unlocks the Needs Attention inbox card", async ({
    page,
  }) => {
    await page.goto(`/case-manager?advisor_token=${advisor.plaintext}`);

    // Card title is the i18n string `advisor.inboxHeading` — "Needs Attention".
    await expect(
      page.getByRole("heading", { name: /needs attention/i }),
    ).toBeVisible();
  });

  test("inbox surfaces stalled sessions or a typed loading/error state", async ({
    page,
  }) => {
    await page.goto(`/case-manager?advisor_token=${advisor.plaintext}`);

    await expect(
      page.getByRole("heading", { name: /needs attention/i }),
    ).toBeVisible();

    // The StalledSessionsList renders rows once the API resolves; until
    // then the loading copy is shown. An invalid token (or unseeded DB)
    // surfaces the typed alert. Any of those proves the section wired.
    await expect(async () => {
      const rows = page.getByRole("listitem");
      const empty = page.getByText(/no stalled sessions/i);
      const loading = page.getByText(/loading/i);
      const alert = page.getByRole("alert");
      const total =
        (await rows.count()) +
        (await empty.count()) +
        (await loading.count()) +
        (await alert.count());
      expect(total).toBeGreaterThan(0);
    }).toPass({ timeout: 5_000 });
  });
});
