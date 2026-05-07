import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

/**
 * Tests for `/admin/assessments` list page (T23.7).
 *
 * Covers:
 *   - Auth guard redirect when useAccount() resolves to anonymous
 *   - Renders the pending-list rows with slug / track / kind / status
 *   - Filter dropdowns narrow the visible rows client-side
 *   - Row click navigates to /admin/assessments/{versionId}
 */

// Router mock — captured here so tests can assert push() calls.
const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: pushMock }),
}));

// Mock the API client + the auth hook the local guard reads.
vi.mock("@/lib/api/assessments", () => ({
  listPendingAssessments: vi.fn(),
}));
vi.mock("@/lib/api/auth", () => ({
  useAccount: vi.fn(),
}));

import { listPendingAssessments } from "@/lib/api/assessments";
import { useAccount } from "@/lib/api/auth";
import AssessmentsListPage from "@/app/admin/assessments/page";

const mockedList = listPendingAssessments as ReturnType<typeof vi.fn>;
const mockedUseAccount = useAccount as unknown as ReturnType<typeof vi.fn>;

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <AssessmentsListPage />
    </QueryClientProvider>,
  );
}

const SAMPLE_ROWS = [
  {
    version_id: 11,
    assessment_id: 1,
    version_number: 2,
    status: "draft",
    drafted_by: 7,
    created_at: "2026-05-01T00:00:00Z",
    slug: "vocational-screen-v2",
    kind: "screening",
    track: "vocational",
  },
  {
    version_id: 12,
    assessment_id: 2,
    version_number: 1,
    status: "in_review",
    drafted_by: 7,
    created_at: "2026-05-01T01:00:00Z",
    slug: "dao-tech-onboarding",
    kind: "onboarding",
    track: "dao_tech",
  },
];

function signedIn() {
  mockedUseAccount.mockReturnValue({
    data: { accountId: 1, email: "reviewer@example.com" },
    isLoading: false,
  });
}

describe("AssessmentsListPage (/admin/assessments)", () => {
  beforeEach(() => {
    pushMock.mockReset();
    mockedList.mockReset();
    mockedUseAccount.mockReset();
  });

  it("redirects to /auth/login when useAccount returns anonymous", async () => {
    mockedUseAccount.mockReturnValue({
      data: { accountId: null, email: null },
      isLoading: false,
    });
    mockedList.mockResolvedValueOnce([]);
    renderPage();
    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/auth/login");
    });
  });

  it("renders pending rows once the query resolves", async () => {
    signedIn();
    mockedList.mockResolvedValueOnce(SAMPLE_ROWS);
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("vocational-screen-v2")).toBeInTheDocument();
    });
    expect(screen.getByText("dao-tech-onboarding")).toBeInTheDocument();
  });

  it("filters rows by track", async () => {
    signedIn();
    mockedList.mockResolvedValueOnce(SAMPLE_ROWS);
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("vocational-screen-v2")).toBeInTheDocument();
    });
    await user.selectOptions(
      screen.getByLabelText(/track/i),
      "vocational",
    );
    expect(screen.getByText("vocational-screen-v2")).toBeInTheDocument();
    expect(screen.queryByText("dao-tech-onboarding")).not.toBeInTheDocument();
  });

  it("filters rows by kind", async () => {
    signedIn();
    mockedList.mockResolvedValueOnce(SAMPLE_ROWS);
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("vocational-screen-v2")).toBeInTheDocument();
    });
    await user.selectOptions(screen.getByLabelText(/kind/i), "onboarding");
    expect(screen.queryByText("vocational-screen-v2")).not.toBeInTheDocument();
    expect(screen.getByText("dao-tech-onboarding")).toBeInTheDocument();
  });

  it("filters rows by status", async () => {
    signedIn();
    mockedList.mockResolvedValueOnce(SAMPLE_ROWS);
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("vocational-screen-v2")).toBeInTheDocument();
    });
    await user.selectOptions(screen.getByLabelText(/status/i), "in_review");
    expect(screen.queryByText("vocational-screen-v2")).not.toBeInTheDocument();
    expect(screen.getByText("dao-tech-onboarding")).toBeInTheDocument();
  });

  it("navigates to detail page when a row is clicked", async () => {
    signedIn();
    mockedList.mockResolvedValueOnce(SAMPLE_ROWS);
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("vocational-screen-v2")).toBeInTheDocument();
    });
    await user.click(
      screen.getByRole("button", { name: /vocational-screen-v2/i }),
    );
    expect(pushMock).toHaveBeenCalledWith("/admin/assessments/11");
  });

  it("renders an empty-state when the queue is empty", async () => {
    signedIn();
    mockedList.mockResolvedValueOnce([]);
    renderPage();
    await waitFor(() => {
      expect(
        screen.getByText(/no pending assessments|nothing to review/i),
      ).toBeInTheDocument();
    });
  });
});
