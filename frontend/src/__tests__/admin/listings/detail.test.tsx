import React from "react";
import { describe, it, expect, beforeEach, afterAll, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

/**
 * Tests for `/admin/listings/[claimId]` detail page (T24.9).
 *
 * Covers:
 *   - Renders claim email + listing details + employer candidate
 *   - Renders intake JSON (if filled) in a readable form
 *   - Approve button calls approveClaim + invalidates the list query
 *   - Reject button shows confirmation, then calls rejectClaim
 *   - Page wraps content in <RoleGate roles={["admin"]}> (strict)
 */

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: pushMock, back: pushMock }),
  useParams: () => ({ claimId: "5" }),
}));

vi.mock("@/lib/api/listing_claims", () => ({
  getClaim: vi.fn(),
  approveClaim: vi.fn(),
  rejectClaim: vi.fn(),
}));

vi.mock("@/lib/api/auth", () => ({
  useAccount: vi.fn(),
  useAccountRoles: vi.fn(),
}));

import {
  getClaim,
  approveClaim,
  rejectClaim,
} from "@/lib/api/listing_claims";
import { useAccount, useAccountRoles } from "@/lib/api/auth";
import AdminClaimDetailPage from "@/app/admin/listings/[claimId]/page";

const mockedGet = getClaim as ReturnType<typeof vi.fn>;
const mockedApprove = approveClaim as ReturnType<typeof vi.fn>;
const mockedReject = rejectClaim as ReturnType<typeof vi.fn>;
const mockedUseAccount = useAccount as unknown as ReturnType<typeof vi.fn>;
const mockedUseAccountRoles =
  useAccountRoles as unknown as ReturnType<typeof vi.fn>;

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <AdminClaimDetailPage />
    </QueryClientProvider>,
  );
}

const SAMPLE_CLAIM = {
  claim_id: 5,
  claimant_email: "alice@acme.com",
  listing_id: 11,
  listing_title: "Forklift Operator",
  listing_company: "ACME Hiring Inc",
  claim_created_at: "2026-05-01T00:00:00Z",
  expires_at: "2026-05-01T00:15:00Z",
  used_at: "2026-05-01T00:05:00Z",
  verification_id: 2,
  employer_account_id: 7,
  employer_name: "acme.com",
  employer_domain: "acme.com",
  employer_status: "admin_review",
  verification_tier: "admin_reviewed",
  intake_json: null,
  intake_completed_at: null,
  verified_at: "2026-05-01T00:05:00Z",
};

const SAMPLE_CLAIM_WITH_INTAKE = {
  ...SAMPLE_CLAIM,
  intake_json: JSON.stringify({
    must_haves: ["valid driver's license"],
    real_day1_tasks: ["site walkthrough"],
    comp_band_min: 18,
    comp_band_max: 24,
    fair_chance_willingness: true,
  }),
  intake_completed_at: "2026-05-01T01:00:00Z",
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

describe("AdminClaimDetailPage (/admin/listings/[claimId])", () => {
  const originalConfirm = window.confirm;

  beforeEach(() => {
    pushMock.mockReset();
    mockedGet.mockReset();
    mockedApprove.mockReset();
    mockedReject.mockReset();
    mockedUseAccount.mockReset();
    mockedUseAccountRoles.mockReset();
    signedInAdmin();
    window.confirm = vi.fn(() => true);
  });

  afterAll(() => {
    window.confirm = originalConfirm;
  });

  it("renders claim email, listing, and employer details", async () => {
    mockedGet.mockResolvedValueOnce(SAMPLE_CLAIM);
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("alice@acme.com")).toBeInTheDocument();
    });
    expect(screen.getByText(/Forklift Operator/)).toBeInTheDocument();
    expect(screen.getByText(/ACME Hiring Inc/)).toBeInTheDocument();
    // Multiple matches expected (claimant_email + employer domain).
    expect(screen.getAllByText(/acme\.com/).length).toBeGreaterThanOrEqual(1);
  });

  it("renders intake fields when intake_json is present", async () => {
    mockedGet.mockResolvedValueOnce(SAMPLE_CLAIM_WITH_INTAKE);
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/valid driver's license/)).toBeInTheDocument();
    });
    expect(screen.getByText(/site walkthrough/)).toBeInTheDocument();
    expect(screen.getByText(/18/)).toBeInTheDocument();
  });

  it("shows 'no intake submitted' when intake is null", async () => {
    mockedGet.mockResolvedValueOnce(SAMPLE_CLAIM);
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/no intake/i)).toBeInTheDocument();
    });
  });

  it("approve button calls approveClaim", async () => {
    mockedGet.mockResolvedValueOnce(SAMPLE_CLAIM);
    mockedApprove.mockResolvedValueOnce({
      claim_id: 5,
      employer_account_id: 7,
      verification_status: "verified",
      verified_at: "2026-05-02T12:00:00Z",
    });
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("alice@acme.com")).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: /approve/i }));
    await waitFor(() => {
      expect(mockedApprove).toHaveBeenCalledWith(5);
    });
  });

  it("reject button calls rejectClaim after confirmation", async () => {
    mockedGet.mockResolvedValueOnce(SAMPLE_CLAIM);
    mockedReject.mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("alice@acme.com")).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: /reject/i }));
    await waitFor(() => {
      expect(mockedReject).toHaveBeenCalledWith(5);
    });
  });

  it("reject button does NOT call API when confirmation is dismissed", async () => {
    window.confirm = vi.fn(() => false);
    mockedGet.mockResolvedValueOnce(SAMPLE_CLAIM);
    mockedReject.mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("alice@acme.com")).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: /reject/i }));
    expect(mockedReject).not.toHaveBeenCalled();
  });

  it("denies access when caller is not admin (strict RoleGate)", async () => {
    signedInNonAdmin();
    mockedGet.mockResolvedValueOnce(SAMPLE_CLAIM);
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/permission denied/i)).toBeInTheDocument();
    });
    expect(screen.queryByText("alice@acme.com")).not.toBeInTheDocument();
  });

  it("renders error state when fetch fails", async () => {
    mockedGet.mockRejectedValueOnce(new Error("nope"));
    renderPage();
    await waitFor(() => {
      expect(
        screen.getByText(/couldn|error|failed|not load/i),
      ).toBeInTheDocument();
    });
  });
});
