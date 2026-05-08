import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

/**
 * Tests for `/admin/listings` list page (T24.9).
 *
 * Covers:
 *   - Renders the pending-claim rows with claimant_email + listing
 *   - Empty-state when the queue is empty
 *   - Filter dropdowns (source / age) narrow the visible rows
 *   - Row click navigates to /admin/listings/{claimId}
 *   - Page wraps content in <RoleGate roles={["admin"]}> (strict)
 */

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: pushMock }),
}));

// Mock the API client. Layout already wraps in RoleGate roles=admin/case_manager/...,
// but the page adds a stricter <RoleGate roles=["admin"]> on top.
vi.mock("@/lib/api/listing_claims", () => ({
  listPendingClaims: vi.fn(),
}));

// Mock useAccount + useAccountRoles so the inner RoleGate evaluates.
vi.mock("@/lib/api/auth", () => ({
  useAccount: vi.fn(),
  useAccountRoles: vi.fn(),
}));

import { listPendingClaims } from "@/lib/api/listing_claims";
import { useAccount, useAccountRoles } from "@/lib/api/auth";
import AdminListingsPage from "@/app/admin/listings/page";

const mockedList = listPendingClaims as ReturnType<typeof vi.fn>;
const mockedUseAccount = useAccount as unknown as ReturnType<typeof vi.fn>;
const mockedUseAccountRoles =
  useAccountRoles as unknown as ReturnType<typeof vi.fn>;

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <AdminListingsPage />
    </QueryClientProvider>,
  );
}

const SAMPLE_ROWS = [
  {
    claim_id: 5,
    claimant_email: "alice@acme.com",
    listing_id: 11,
    listing_title: "Forklift",
    employer_account_id: 7,
    employer_name: "acme.com",
    employer_domain: "acme.com",
    verification_tier: "admin_reviewed",
    intake_completed_at: null,
    verification_id: 2,
    verification_created_at: "2026-05-01T00:00:00Z",
    claim_created_at: "2026-05-01T00:00:00Z",
  },
  {
    claim_id: 6,
    claimant_email: "bob@beta.org",
    listing_id: 12,
    listing_title: "Cook",
    employer_account_id: 8,
    employer_name: "beta.org",
    employer_domain: "beta.org",
    verification_tier: "admin_reviewed",
    intake_completed_at: "2026-05-02T00:00:00Z",
    verification_id: 3,
    verification_created_at: "2026-05-02T00:00:00Z",
    claim_created_at: "2026-05-02T00:00:00Z",
  },
];

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

describe("AdminListingsPage (/admin/listings)", () => {
  beforeEach(() => {
    pushMock.mockReset();
    mockedList.mockReset();
    mockedUseAccount.mockReset();
    mockedUseAccountRoles.mockReset();
    signedInAdmin();
  });

  it("renders pending claim rows once the query resolves", async () => {
    mockedList.mockResolvedValueOnce(SAMPLE_ROWS);
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("alice@acme.com")).toBeInTheDocument();
    });
    expect(screen.getByText("bob@beta.org")).toBeInTheDocument();
  });

  it("renders an empty-state when the queue is empty", async () => {
    mockedList.mockResolvedValueOnce([]);
    renderPage();
    await waitFor(() => {
      expect(
        screen.getByText(/no pending|nothing to review/i),
      ).toBeInTheDocument();
    });
  });

  it("filters rows by intake (with-intake / no-intake)", async () => {
    mockedList.mockResolvedValueOnce(SAMPLE_ROWS);
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("alice@acme.com")).toBeInTheDocument();
    });
    await user.selectOptions(screen.getByLabelText(/intake/i), "with_intake");
    expect(screen.queryByText("alice@acme.com")).not.toBeInTheDocument();
    expect(screen.getByText("bob@beta.org")).toBeInTheDocument();
  });

  it("filters rows by no-intake", async () => {
    mockedList.mockResolvedValueOnce(SAMPLE_ROWS);
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("alice@acme.com")).toBeInTheDocument();
    });
    await user.selectOptions(screen.getByLabelText(/intake/i), "no_intake");
    expect(screen.getByText("alice@acme.com")).toBeInTheDocument();
    expect(screen.queryByText("bob@beta.org")).not.toBeInTheDocument();
  });

  it("navigates to detail page when a row is clicked", async () => {
    mockedList.mockResolvedValueOnce(SAMPLE_ROWS);
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("alice@acme.com")).toBeInTheDocument();
    });
    await user.click(
      screen.getByRole("button", { name: /alice@acme\.com/i }),
    );
    expect(pushMock).toHaveBeenCalledWith("/admin/listings/5");
  });

  it("denies access when caller is not admin (strict RoleGate)", async () => {
    signedInNonAdmin();
    mockedList.mockResolvedValueOnce(SAMPLE_ROWS);
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/permission denied/i)).toBeInTheDocument();
    });
    expect(screen.queryByText("alice@acme.com")).not.toBeInTheDocument();
  });
});
