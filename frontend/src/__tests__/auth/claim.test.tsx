import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock next/navigation BEFORE importing the page so the hook is replaced
// at module-eval time. Each test sets the search-string before render.
let mockSearch = "";
vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(mockSearch),
}));

vi.mock("@/lib/api/auth", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/auth")>(
    "@/lib/api/auth",
  );
  return {
    ...actual,
    claimMagicLink: vi.fn(),
  };
});

import { claimMagicLink, ClaimError } from "@/lib/api/auth";
import ClaimPage from "@/app/auth/claim/page";

const mockedClaim = claimMagicLink as ReturnType<typeof vi.fn>;

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ClaimPage />
    </QueryClientProvider>,
  );
}

describe("ClaimPage (/auth/claim)", () => {
  beforeEach(() => {
    mockedClaim.mockReset();
    mockSearch = "";
  });

  it("renders the invalid-token state when no token is in the URL", async () => {
    mockSearch = "";
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/invalid|expired/i)).toBeInTheDocument();
    });
    expect(mockedClaim).not.toHaveBeenCalled();
  });

  it("shows a loading state while the claim is in flight", () => {
    mockSearch = "?token=abc";
    mockedClaim.mockImplementationOnce(() => new Promise(() => {}));
    renderPage();
    expect(screen.getByText(/signing you in|verifying|finishing/i)).toBeInTheDocument();
  });

  it("renders the success state with the claimed account id", async () => {
    mockSearch = "?token=good";
    mockedClaim.mockResolvedValueOnce({
      account_id: 42,
      claimed_session_ids: ["sess-1", "sess-2"],
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/you're signed in|signed in|welcome/i)).toBeInTheDocument();
    });
    expect(mockedClaim).toHaveBeenCalledWith("good");
  });

  it("renders the invalid-token state on a 401 ClaimError", async () => {
    mockSearch = "?token=bad";
    mockedClaim.mockRejectedValueOnce(new ClaimError("invalid", 401));
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/invalid|expired/i)).toBeInTheDocument();
    });
    // Provides a way to request a fresh link
    expect(screen.getByRole("link", { name: /request a new link|sign in/i })).toBeInTheDocument();
  });

  it("renders the conflict state on a 409 ClaimError", async () => {
    mockSearch = "?token=conf";
    mockedClaim.mockRejectedValueOnce(new ClaimError("conflict", 409));
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/session is already linked/i)).toBeInTheDocument();
    });
    expect(
      screen.getByRole("link", { name: /sign in with another email/i }),
    ).toBeInTheDocument();
  });

  it("renders a generic error on an unknown failure", async () => {
    mockSearch = "?token=x";
    mockedClaim.mockRejectedValueOnce(new ClaimError("unknown", 500));
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    });
    expect(screen.getByRole("link", { name: /back to sign-in/i })).toBeInTheDocument();
  });
});
