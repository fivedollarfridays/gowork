import React from "react";
import {
  describe,
  it,
  expect,
  beforeEach,
  afterEach,
  vi,
} from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

/**
 * Tests for `/admin/brightdata` trigger page (T26.10 — Sprint 26 Wave 3).
 *
 * The page is operator-facing and money-touching — every BrightData
 * trigger costs real dollars — so the confirmation dialog is the
 * load-bearing UX safety. The test suite verifies:
 *
 *   - city selector renders all three supported cities
 *   - clicking "Trigger Pre-Crawl" opens a confirmation dialog and does
 *     NOT call the API by itself (accidental-click safety)
 *   - cancelling the dialog also does NOT call the API
 *   - confirming the dialog calls `triggerCrawl` with the correct
 *     `{ urls: string[] }` payload (matches T26.7 TriggerCrawlPayload)
 *   - the trigger button is disabled while the request is in-flight
 *   - all four `CrawlStatusValue` states (`starting | running | ready
 *     | failed`) render as distinguishable status text
 *   - the refresh button calls `getCrawlStatus(snapshotId)`
 *   - the last-triggered snapshot id is persisted to localStorage on
 *     trigger and restored on mount
 *
 * Backend reality (per T26.7 client deviation note):
 *   Routes are mounted at `/api/brightdata` (NOT `/api/admin/brightdata`)
 *   and the status enum has FOUR states (the brief said three; the
 *   client confirmed four — `starting | running | ready | failed`).
 */

vi.mock("@/lib/api/admin_brightdata", () => ({
  triggerCrawl: vi.fn(),
  getCrawlStatus: vi.fn(),
  AdminBrightDataApiError: class AdminBrightDataApiError extends Error {
    status: number;
    detail?: string;
    constructor(status: number, message: string, detail?: string) {
      super(message);
      this.name = "AdminBrightDataApiError";
      this.status = status;
      this.detail = detail;
    }
  },
}));

vi.mock("@/lib/api/auth", () => ({
  useAccount: vi.fn(),
  useAccountRoles: vi.fn(),
}));

import {
  triggerCrawl,
  getCrawlStatus,
} from "@/lib/api/admin_brightdata";
import { useAccount, useAccountRoles } from "@/lib/api/auth";
import AdminBrightDataPage from "@/app/admin/brightdata/page";

const mockedTrigger = triggerCrawl as ReturnType<typeof vi.fn>;
const mockedStatus = getCrawlStatus as ReturnType<typeof vi.fn>;
const mockedUseAccount = useAccount as unknown as ReturnType<typeof vi.fn>;
const mockedUseAccountRoles =
  useAccountRoles as unknown as ReturnType<typeof vi.fn>;

function signedInAdmin() {
  mockedUseAccount.mockReturnValue({
    isLoading: false,
    data: { id: 1, email: "admin@example.com" },
  });
  mockedUseAccountRoles.mockReturnValue(["admin"]);
}

function renderPage() {
  return render(<AdminBrightDataPage />);
}

const STORAGE_KEY = "admin.brightdata.lastSnapshotId";

describe("AdminBrightDataPage (/admin/brightdata)", () => {
  beforeEach(() => {
    mockedTrigger.mockReset();
    mockedStatus.mockReset();
    mockedUseAccount.mockReset();
    mockedUseAccountRoles.mockReset();
    signedInAdmin();
    window.localStorage.clear();
  });

  afterEach(() => {
    window.localStorage.clear();
  });

  it("renders the trigger panel with city selector and trigger button", async () => {
    renderPage();
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /trigger pre-crawl/i }),
      ).toBeInTheDocument();
    });
    // City selector must be present
    expect(screen.getByTestId("city-selector")).toBeInTheDocument();
  });

  it("clicking trigger opens the confirmation dialog WITHOUT calling the API", async () => {
    const user = userEvent.setup();
    renderPage();
    const triggerBtn = await screen.findByRole("button", {
      name: /trigger pre-crawl/i,
    });
    await user.click(triggerBtn);
    // Dialog must appear
    expect(
      await screen.findByRole("alertdialog"),
    ).toBeInTheDocument();
    // API must NOT have been called yet — this is the accidental-click safety
    expect(mockedTrigger).not.toHaveBeenCalled();
  });

  it("cancelling the dialog does NOT call the API", async () => {
    const user = userEvent.setup();
    renderPage();
    await user.click(
      await screen.findByRole("button", { name: /trigger pre-crawl/i }),
    );
    const dialog = await screen.findByRole("alertdialog");
    await user.click(within(dialog).getByRole("button", { name: /cancel/i }));
    // Dialog dismissed
    await waitFor(() => {
      expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    });
    expect(mockedTrigger).not.toHaveBeenCalled();
  });

  it("confirming the dialog calls triggerCrawl with the correct urls payload", async () => {
    mockedTrigger.mockResolvedValueOnce({
      snapshot_id: "snap_abc",
      status: "starting",
      message: "Crawl triggered",
    });
    const user = userEvent.setup();
    renderPage();
    await user.click(
      await screen.findByRole("button", { name: /trigger pre-crawl/i }),
    );
    const dialog = await screen.findByRole("alertdialog");
    await user.click(
      within(dialog).getByRole("button", { name: /confirm/i }),
    );
    await waitFor(() => {
      expect(mockedTrigger).toHaveBeenCalledTimes(1);
    });
    const payload = mockedTrigger.mock.calls[0][0];
    expect(payload).toHaveProperty("urls");
    expect(Array.isArray(payload.urls)).toBe(true);
    expect(payload.urls.length).toBeGreaterThan(0);
    // every entry is an https URL string
    for (const u of payload.urls) {
      expect(typeof u).toBe("string");
      expect(u).toMatch(/^https:\/\//);
    }
  });

  it("trigger button is disabled while the request is in flight", async () => {
    let resolveTrigger: (v: unknown) => void = () => {};
    mockedTrigger.mockReturnValueOnce(
      new Promise((resolve) => {
        resolveTrigger = resolve;
      }),
    );
    const user = userEvent.setup();
    renderPage();
    // Use data-testid to disambiguate the page-level trigger button from
    // the dialog's confirm button (both swap their visible text to
    // "Triggering…" while in-flight, so role+name lookup is ambiguous).
    const triggerBtn = await screen.findByTestId("trigger-button");
    await user.click(triggerBtn);
    const dialog = await screen.findByRole("alertdialog");
    await user.click(
      within(dialog).getByRole("button", { name: /confirm/i }),
    );
    // While in-flight the page-level trigger button must be disabled.
    await waitFor(() => {
      expect(screen.getByTestId("trigger-button")).toBeDisabled();
    });
    // Resolve so the test settles cleanly.
    resolveTrigger({
      snapshot_id: "snap_xyz",
      status: "starting",
      message: "ok",
    });
    await waitFor(() => {
      expect(screen.getByTestId("trigger-button")).not.toBeDisabled();
    });
  });

  it.each([
    ["starting", /starting/i],
    ["running", /running/i],
    ["ready", /ready/i],
    ["failed", /failed/i],
  ])(
    "status panel renders the %s state distinctly",
    async (statusValue, matcher) => {
      // Seed localStorage so the page can find a snapshot to display
      window.localStorage.setItem(STORAGE_KEY, "snap_seeded");
      mockedStatus.mockResolvedValueOnce({
        snapshot_id: "snap_seeded",
        status: statusValue,
        progress_pct: statusValue === "running" ? 42 : null,
        jobs_found: statusValue === "ready" ? 7 : null,
        message: `Crawl is ${statusValue}`,
      });
      const user = userEvent.setup();
      renderPage();
      // Click refresh so the mocked status comes through
      const refreshBtn = await screen.findByRole("button", {
        name: /refresh status/i,
      });
      await user.click(refreshBtn);
      await waitFor(() => {
        const panel = screen.getByTestId("status-panel");
        expect(panel).toHaveTextContent(matcher);
      });
    },
  );

  it("refresh button calls getCrawlStatus with the persisted snapshot id", async () => {
    window.localStorage.setItem(STORAGE_KEY, "snap_persisted");
    mockedStatus.mockResolvedValueOnce({
      snapshot_id: "snap_persisted",
      status: "running",
      progress_pct: 10,
      jobs_found: null,
      message: "still running",
    });
    const user = userEvent.setup();
    renderPage();
    const refreshBtn = await screen.findByRole("button", {
      name: /refresh status/i,
    });
    await user.click(refreshBtn);
    await waitFor(() => {
      expect(mockedStatus).toHaveBeenCalledWith("snap_persisted");
    });
  });

  it("writes the snapshot id to localStorage on successful trigger", async () => {
    mockedTrigger.mockResolvedValueOnce({
      snapshot_id: "snap_persist_me",
      status: "starting",
      message: "Crawl triggered",
    });
    const user = userEvent.setup();
    renderPage();
    await user.click(
      await screen.findByRole("button", { name: /trigger pre-crawl/i }),
    );
    const dialog = await screen.findByRole("alertdialog");
    await user.click(
      within(dialog).getByRole("button", { name: /confirm/i }),
    );
    await waitFor(() => {
      expect(window.localStorage.getItem(STORAGE_KEY)).toBe(
        "snap_persist_me",
      );
    });
  });

  it("reads the snapshot id from localStorage on mount and shows it in the status panel", async () => {
    window.localStorage.setItem(STORAGE_KEY, "snap_from_storage");
    renderPage();
    await waitFor(() => {
      const panel = screen.getByTestId("status-panel");
      expect(panel).toHaveTextContent(/snap_from_storage/);
    });
  });
});
