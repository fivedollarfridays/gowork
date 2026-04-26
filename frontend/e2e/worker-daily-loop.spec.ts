import { test, expect } from "@playwright/test";
import { DEMO, detectBackend, workerAuthQuery } from "./_demo_session";

/**
 * Beat 2 of the demo script — worker arrives at the morning digest via
 * a tokenized URL (mirrors the email/SMS unsubscribe-style auth where a
 * worker clicks a link from their device).
 *
 * The page is gated on session_id + feedback_token (URL params, then
 * sessionStorage cache via `useSessionId`/`useToken`). We pass them on
 * the URL on every navigation so each test is independent.
 *
 * Backend dependency: the digest endpoint (T12.21a) must respond. We
 * pre-flight `/health` so a missing/wrong backend skips with a clear
 * message rather than failing the run for unrelated reasons. The
 * canonical fixtures come from `python scripts/qc_reset.py`.
 */
test.describe("@critical worker daily loop", () => {
  const creds = DEMO.workerMontgomeryMedium;

  test.beforeAll(async ({ request }) => {
    const reason = await detectBackend(request);
    test.skip(reason !== null, reason ?? "");
  });

  test("daily page renders the digest title for an authed session", async ({
    page,
  }) => {
    await page.goto(`/daily?${workerAuthQuery(creds)}`);

    // Title from i18n key `digest.page.title` ("Your daily digest").
    await expect(
      page.getByRole("heading", { level: 1, name: /your daily digest/i }),
    ).toBeVisible();
  });

  test("daily page surfaces digest sections or a typed error", async ({
    page,
  }) => {
    await page.goto(`/daily?${workerAuthQuery(creds)}`);

    // The page settles in one of three states. Any of those proves the
    // page wired session + token through the useSession hooks and
    // dispatched a network request.
    await expect(async () => {
      const sections = page.getByRole("heading", { level: 2 });
      const alert = page.getByRole("alert");
      const loaders = page.getByText(/loading/i);
      const total =
        (await sections.count()) +
        (await alert.count()) +
        (await loaders.count());
      expect(total).toBeGreaterThan(0);
    }).toPass({ timeout: 5_000 });
  });

  test("daily page reachable for an authed session (no 5xx, no JS crash)", async ({
    page,
  }) => {
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(err.message));

    const response = await page.goto(`/daily?${workerAuthQuery(creds)}`);
    expect(response?.ok()).toBe(true);
    expect(errors).toEqual([]);
  });
});
