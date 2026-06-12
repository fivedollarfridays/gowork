import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  render,
  screen,
  waitFor,
  within,
  fireEvent,
  act,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

/**
 * Tests for `/admin/feedback` tabbed page (T26.9 — Sprint 26 Wave 3).
 *
 * Page composition:
 *   - shadcn ``Tabs`` with two ``TabsTrigger``s — "Flagged Resources"
 *     (default) and "Visit Feedback".
 *   - URL hash sync: ``#flagged`` / ``#visits`` selects the matching
 *     tab on mount so deep links Just Work.
 *
 * Tab content (split into FlaggedResourcesTab + VisitFeedbackTab for
 * testability — see ``components/admin/FeedbackTabs.tsx``):
 *
 *   - FlaggedResourcesTab renders a card per flagged resource with a
 *     name + recent-negative-feedback excerpts; row actions invoke
 *     ``approveFlagged`` / ``confirmHide`` then refetch the list.
 *
 *   - VisitFeedbackTab renders a table (submitted_at, made-it-to-center
 *     badge, plan-accuracy stars, free_text excerpt, reviewed badge,
 *     action_taken summary), a filter dropdown
 *     (all / reviewed / unreviewed), and a Mark Reviewed row action
 *     with an optional ``action_taken`` textarea.
 *
 * Both tabs paginate independently (50 per page; prev/next).
 *
 * The shared ``/admin/layout.tsx`` already wraps every ``/admin/*``
 * page in ``<RoleGate>`` — this page mounts the same strict-admin gate
 * inside its inner shell so non-admin reviewers get a "Permission
 * denied" card instead of an empty queue. We assert role denial here
 * to keep the gate from drifting silently.
 */

vi.mock("@/lib/api/admin_feedback", () => ({
  listFlagged: vi.fn(),
  approveFlagged: vi.fn(),
  confirmHide: vi.fn(),
  listVisits: vi.fn(),
  markVisitReviewed: vi.fn(),
}));

vi.mock("@/lib/api/auth", () => ({
  useAccount: vi.fn(),
  useAccountRoles: vi.fn(),
}));

import {
  listFlagged,
  approveFlagged,
  confirmHide,
  listVisits,
  markVisitReviewed,
} from "@/lib/api/admin_feedback";
import { useAccount, useAccountRoles } from "@/lib/api/auth";
import AdminFeedbackPage from "@/app/admin/feedback/page";

const mockedListFlagged = listFlagged as ReturnType<typeof vi.fn>;
const mockedApprove = approveFlagged as ReturnType<typeof vi.fn>;
const mockedConfirmHide = confirmHide as ReturnType<typeof vi.fn>;
const mockedListVisits = listVisits as ReturnType<typeof vi.fn>;
const mockedMarkReviewed = markVisitReviewed as ReturnType<typeof vi.fn>;
const mockedUseAccount = useAccount as unknown as ReturnType<typeof vi.fn>;
const mockedUseAccountRoles =
  useAccountRoles as unknown as ReturnType<typeof vi.fn>;

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <AdminFeedbackPage />
    </QueryClientProvider>,
  );
}

const SAMPLE_FLAGGED = {
  items: [
    {
      id: 11,
      name: "Acme Childcare",
      category: "childcare",
      city: "fort-worth",
      health_status: "flagged",
      address: "100 Main",
      phone: "555-0100",
      url: "https://acme.example",
      recent_negative_feedback: [
        {
          session_id: "sess-A",
          barrier_type: "closed",
          submitted_at: "2026-04-30T10:00:00Z",
        },
      ],
    },
    {
      id: 12,
      name: "Beta Career Hub",
      category: "career_center",
      city: "fort-worth",
      health_status: "flagged",
      address: null,
      phone: null,
      url: null,
      recent_negative_feedback: [],
    },
  ],
};

const SAMPLE_VISITS = {
  items: [
    {
      id: 501,
      session_id: "s-501",
      submitted_at: "2026-05-01T12:00:00Z",
      made_it_to_center: 1,
      outcomes: "got benefits",
      plan_accuracy: 4,
      free_text: "Plan worked great!",
      reviewed: 0,
      action_taken: null,
    },
    {
      id: 502,
      session_id: "s-502",
      submitted_at: "2026-05-02T09:30:00Z",
      made_it_to_center: 0,
      outcomes: null,
      plan_accuracy: 2,
      free_text: "Center was closed",
      reviewed: 1,
      action_taken: "Updated hours",
    },
  ],
  total: 2,
  limit: 50,
  offset: 0,
};

function signedInAdmin() {
  mockedUseAccount.mockReturnValue({
    isLoading: false,
    data: { id: 1, email: "admin@example.com" },
  });
  mockedUseAccountRoles.mockReturnValue(["admin"]);
}

function signedInNonAdmin() {
  mockedUseAccount.mockReturnValue({
    isLoading: false,
    data: { id: 1, email: "user@example.com" },
  });
  mockedUseAccountRoles.mockReturnValue(["case_manager"]);
}

function setHash(hash: string) {
  // jsdom's location is read-only via assignment, but `window.location.hash`
  // is settable. Use act so React picks up the resulting popstate listener
  // synchronously inside the test boundary.
  act(() => {
    window.location.hash = hash;
  });
}

describe("AdminFeedbackPage (/admin/feedback)", () => {
  beforeEach(() => {
    mockedListFlagged.mockReset();
    mockedApprove.mockReset();
    mockedConfirmHide.mockReset();
    mockedListVisits.mockReset();
    mockedMarkReviewed.mockReset();
    mockedUseAccount.mockReset();
    mockedUseAccountRoles.mockReset();
    signedInAdmin();
    // Reset hash between tests (we mutate it for hash-sync coverage).
    if (typeof window !== "undefined") {
      window.history.replaceState(null, "", window.location.pathname);
    }
    mockedListFlagged.mockResolvedValue(SAMPLE_FLAGGED);
    mockedListVisits.mockResolvedValue(SAMPLE_VISITS);
  });

  it("renders the page header and both tab triggers", async () => {
    renderPage();
    await waitFor(() => {
      expect(
        screen.getByRole("tab", { name: /flagged resources/i }),
      ).toBeInTheDocument();
    });
    expect(
      screen.getByRole("tab", { name: /visit feedback/i }),
    ).toBeInTheDocument();
  });

  it("defaults to the Flagged Resources tab and renders a card per flagged resource", async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByTestId("flagged-card-11")).toBeInTheDocument();
    });
    expect(screen.getByTestId("flagged-card-11")).toHaveTextContent(
      /Acme Childcare/,
    );
    expect(screen.getByTestId("flagged-card-12")).toHaveTextContent(
      /Beta Career Hub/,
    );
  });

  it("Flagged tab Approve button calls approveFlagged with the resource id and refetches", async () => {
    mockedApprove.mockResolvedValueOnce({ id: 11, health_status: "healthy" });
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByTestId("flagged-card-11")).toBeInTheDocument();
    });
    expect(mockedListFlagged).toHaveBeenCalledTimes(1);

    await user.click(
      within(screen.getByTestId("flagged-card-11")).getByRole("button", {
        name: /approve/i,
      }),
    );
    await waitFor(() => {
      expect(mockedApprove).toHaveBeenCalledWith(11);
    });
    await waitFor(() => {
      expect(mockedListFlagged).toHaveBeenCalledTimes(2);
    });
  });

  it("Flagged tab Confirm Hide button calls confirmHide with the resource id and refetches", async () => {
    mockedConfirmHide.mockResolvedValueOnce({ id: 12, health_status: "hidden" });
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByTestId("flagged-card-12")).toBeInTheDocument();
    });

    await user.click(
      within(screen.getByTestId("flagged-card-12")).getByRole("button", {
        name: /confirm hide/i,
      }),
    );
    await waitFor(() => {
      expect(mockedConfirmHide).toHaveBeenCalledWith(12);
    });
    await waitFor(() => {
      expect(mockedListFlagged).toHaveBeenCalledTimes(2);
    });
  });

  it("clicking the Visit Feedback tab swaps to the visits table", async () => {
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByTestId("flagged-card-11")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("tab", { name: /visit feedback/i }));

    await waitFor(() => {
      expect(screen.getByTestId("visit-row-501")).toBeInTheDocument();
    });
    expect(screen.getByTestId("visit-row-501")).toHaveTextContent(
      /Plan worked great/,
    );
    expect(screen.getByTestId("visit-row-502")).toHaveTextContent(
      /Center was closed/,
    );
  });

  it("URL hash #visits activates the Visit Feedback tab on mount", async () => {
    setHash("#visits");
    renderPage();
    await waitFor(() => {
      expect(screen.getByTestId("visit-row-501")).toBeInTheDocument();
    });
    expect(
      screen.getByRole("tab", { name: /visit feedback/i, selected: true }),
    ).toBeInTheDocument();
  });

  it("URL hash #flagged activates the Flagged Resources tab on mount", async () => {
    setHash("#flagged");
    renderPage();
    await waitFor(() => {
      expect(screen.getByTestId("flagged-card-11")).toBeInTheDocument();
    });
    expect(
      screen.getByRole("tab", { name: /flagged resources/i, selected: true }),
    ).toBeInTheDocument();
  });

  it("Mark Reviewed submits the action_taken text via markVisitReviewed", async () => {
    mockedMarkReviewed.mockResolvedValueOnce({
      id: 501,
      reviewed: true,
      action_taken: "Called provider",
    });
    const user = userEvent.setup();
    setHash("#visits");
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId("visit-row-501")).toBeInTheDocument();
    });

    // Open the inline action-taken editor for row 501.
    await user.click(
      within(screen.getByTestId("visit-row-501")).getByRole("button", {
        name: /mark reviewed/i,
      }),
    );

    const textarea = await screen.findByTestId("action-taken-501");
    await act(async () => {
      fireEvent.change(textarea, { target: { value: "Called provider" } });
    });

    await user.click(
      screen.getByRole("button", { name: /submit reviewed/i }),
    );

    await waitFor(() => {
      expect(mockedMarkReviewed).toHaveBeenCalledWith(501, "Called provider");
    });
  });

  it("changing the visit-feedback filter to 'unreviewed' refetches with reviewed=false", async () => {
    const user = userEvent.setup();
    setHash("#visits");
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId("visit-row-501")).toBeInTheDocument();
    });

    const filter = screen.getByLabelText(/filter/i);
    await act(async () => {
      fireEvent.change(filter, { target: { value: "unreviewed" } });
    });

    await waitFor(() => {
      // Last call should now include reviewed=false.
      const lastCall = mockedListVisits.mock.calls.at(-1)?.[0] ?? {};
      expect(lastCall.reviewed).toBe(false);
    });
  });

  it("blocks non-admin callers via the strict RoleGate", async () => {
    signedInNonAdmin();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/permission denied/i)).toBeInTheDocument();
    });
    expect(
      screen.queryByRole("tab", { name: /flagged resources/i }),
    ).not.toBeInTheDocument();
  });
});
