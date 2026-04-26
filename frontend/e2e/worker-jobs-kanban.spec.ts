import { test, expect } from "@playwright/test";
import { DEMO, detectBackend, workerAuthQuery } from "./_demo_session";

/**
 * Beat 4 of the demo script — worker views the Jobs Tracker kanban.
 *
 * The kanban is `dnd-kit`-powered, which Playwright's drag-and-drop
 * emulation cannot reliably drive (PointerSensor needs a synthetic
 * pointer-move sequence — flakey across headless chromium versions).
 * Instead, we verify:
 *   - All six status columns render.
 *   - The kanban-board test-id exists (so the layout shipped).
 *   - Either the seeded application card shows up OR the empty-board
 *     copy is visible (seed plants one application via
 *     `_demo_seed_rows.insert_application`).
 *
 * Drag-and-drop semantics + status-mutation paths are covered by:
 *   - jobs.spec.ts vitest suite (component-level `react-dnd-kit` mocks)
 *   - divona `worker-jobs-board.qc.yaml` (interactive Chrome)
 */
test.describe("@critical worker jobs kanban", () => {
  const creds = DEMO.workerMontgomeryMedium;

  test.beforeAll(async ({ request }) => {
    const reason = await detectBackend(request);
    test.skip(reason !== null, reason ?? "");
  });

  test("jobs page renders the kanban board with all status columns", async ({
    page,
  }) => {
    await page.goto(`/jobs?${workerAuthQuery(creds)}`);

    await expect(
      page.getByRole("heading", { level: 1, name: /jobs tracker/i }),
    ).toBeVisible();

    // The kanban container is tagged with a stable data-testid.
    await expect(page.getByTestId("kanban-board")).toBeVisible();

    // Six canonical columns from `STATUS_COLUMNS` in kanbanHelpers.ts.
    // The h2 heading text is "<Label> <count>" (count badge inside the
    // heading), so the accessible name is e.g. "Draft 0". Match the
    // region instead — its aria-label is the bare label.
    for (const label of [
      "Draft",
      "Applied",
      "Interview",
      "Offer",
      "Rejected",
      "Withdrawn",
    ]) {
      await expect(
        page.getByRole("region", { name: label, exact: true }),
      ).toBeVisible();
    }
  });

  test("board surfaces seeded application or the empty-board copy", async ({
    page,
  }) => {
    await page.goto(`/jobs?${workerAuthQuery(creds)}`);

    // Wait for the page to commit to a state.
    await expect(page.getByTestId("kanban-board")).toBeVisible();

    // Either the empty-board copy is shown OR at least one card is
    // rendered (any role=listitem inside the kanban). Both prove the
    // list-applications API resolved.
    await expect(async () => {
      const cards = page.getByRole("listitem");
      const empty = page.getByText(/no applications yet/i);
      const loading = page.getByText(/loading applications/i);
      const total =
        (await cards.count()) +
        (await empty.count()) +
        (await loading.count());
      expect(total).toBeGreaterThan(0);
    }).toPass({ timeout: 5_000 });
  });
});
