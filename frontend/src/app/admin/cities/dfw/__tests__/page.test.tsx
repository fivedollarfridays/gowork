import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

/**
 * Tests for `/admin/cities/dfw` summary page (T25.7 — Sprint 25 Wave 5).
 *
 * Charter integrity:
 * The page is a read-only diagnostic. The test suite verifies:
 *   - both city cards (Fort Worth, Dallas) render with their counts
 *   - the footer "DFW total" row sums per-card values
 *   - non-admin callers are blocked by the strict <RoleGate> wrapper
 *   - API fetch failures render an error card (not a blank page)
 *
 * The "Read-only diagnostic" header copy is also asserted — that string
 * is the design-review trigger if a future sprint legitimately needs
 * cross-metro matching, so we want to know if it ever drifts.
 */

vi.mock("@/lib/api/cities_admin", () => ({
  getDfwSummary: vi.fn(),
}));

vi.mock("@/lib/api/auth", () => ({
  useAccount: vi.fn(),
  useAccountRoles: vi.fn(),
}));

import { getDfwSummary } from "@/lib/api/cities_admin";
import { useAccount, useAccountRoles } from "@/lib/api/auth";
import AdminCitiesDfwPage from "@/app/admin/cities/dfw/page";

const mockedGet = getDfwSummary as ReturnType<typeof vi.fn>;
const mockedUseAccount = useAccount as unknown as ReturnType<typeof vi.fn>;
const mockedUseAccountRoles =
  useAccountRoles as unknown as ReturnType<typeof vi.fn>;

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <AdminCitiesDfwPage />
    </QueryClientProvider>,
  );
}

const SAMPLE_SUMMARY = {
  cities: [
    {
      slug: "fort-worth",
      name: "Fort Worth",
      state: "TX",
      resource_counts: {
        social_service: 8,
        career_center: 0,
        childcare: 0,
      },
      employer_count: 12,
      fair_chance_count: 8,
      fair_chance_pct: 0.6667,
      transit_route_count: 14,
      transit_stop_count: 42,
      career_center_count: 1,
    },
    {
      slug: "dallas",
      name: "Dallas",
      state: "TX",
      resource_counts: {
        social_service: 9,
        career_center: 7,
        childcare: 1,
      },
      employer_count: 35,
      fair_chance_count: 27,
      fair_chance_pct: 0.7714,
      transit_route_count: 27,
      transit_stop_count: 303,
      career_center_count: 1,
    },
  ],
  dfw_total: {
    resource_counts: {
      social_service: 17,
      career_center: 7,
      childcare: 1,
    },
    employer_count: 47,
    fair_chance_count: 35,
    fair_chance_pct: 0.7447,
    transit_route_count: 41,
    transit_stop_count: 345,
    career_center_count: 2,
  },
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

describe("AdminCitiesDfwPage (/admin/cities/dfw)", () => {
  beforeEach(() => {
    mockedGet.mockReset();
    mockedUseAccount.mockReset();
    mockedUseAccountRoles.mockReset();
    signedInAdmin();
  });

  it("renders the read-only diagnostic header copy", async () => {
    mockedGet.mockResolvedValueOnce(SAMPLE_SUMMARY);
    renderPage();
    await waitFor(() => {
      expect(
        screen.getByText(/read-only diagnostic/i),
      ).toBeInTheDocument();
    });
    expect(
      screen.getByText(/cross-city matching is not enabled/i),
    ).toBeInTheDocument();
  });

  it("renders both city cards (Fort Worth + Dallas) with counts", async () => {
    mockedGet.mockResolvedValueOnce(SAMPLE_SUMMARY);
    renderPage();
    await waitFor(() => {
      expect(screen.getByTestId("city-card-fort-worth")).toBeInTheDocument();
    });
    const fwCard = screen.getByTestId("city-card-fort-worth");
    const dalCard = screen.getByTestId("city-card-dallas");
    expect(fwCard).toHaveTextContent(/Fort Worth/);
    expect(fwCard).toHaveTextContent(/12/); // employer count
    expect(dalCard).toHaveTextContent(/Dallas/);
    expect(dalCard).toHaveTextContent(/35/); // employer count
  });

  it("footer total equals sum of per-city values", async () => {
    mockedGet.mockResolvedValueOnce(SAMPLE_SUMMARY);
    renderPage();
    await waitFor(() => {
      expect(screen.getByTestId("dfw-total-row")).toBeInTheDocument();
    });
    const totalRow = screen.getByTestId("dfw-total-row");
    // employer_count: 12 + 35 = 47
    expect(totalRow).toHaveTextContent(/47/);
    // transit_stop_count: 42 + 303 = 345
    expect(totalRow).toHaveTextContent(/345/);
  });

  it("blocks non-admin callers via the strict RoleGate", async () => {
    signedInNonAdmin();
    mockedGet.mockResolvedValueOnce(SAMPLE_SUMMARY);
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/permission denied/i)).toBeInTheDocument();
    });
    expect(
      screen.queryByTestId("city-card-fort-worth"),
    ).not.toBeInTheDocument();
  });

  it("renders an error card when the fetch fails", async () => {
    mockedGet.mockRejectedValueOnce(new Error("nope"));
    renderPage();
    await waitFor(() => {
      expect(
        screen.getByText(/couldn|error|failed|unable/i),
      ).toBeInTheDocument();
    });
    expect(
      screen.queryByTestId("city-card-fort-worth"),
    ).not.toBeInTheDocument();
  });
});
