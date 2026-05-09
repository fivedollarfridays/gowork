import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

/**
 * Tests for `/admin` landing page (T26.11 — Sprint 26 Wave 4).
 *
 * The landing page is the operator entry point that replaces direct
 * URL navigation across the S23-S26 admin surface. It renders:
 *
 *   - A quick-stats row with four count badges (flagged resources,
 *     unreviewed visit feedback, pending claims, pending assessments).
 *   - Six section cards (Assessments, Listings, Cities/DFW, Resources,
 *     Feedback, BrightData), each with a Next ``<Link>`` to its page.
 *
 * Charter integrity:
 *   The page is display-only. It consumes the four typed admin API
 *   clients (admin_feedback, listing_claims, assessments) and never
 *   imports anything from ``backend/app/modules/matching/``. Any future
 *   matching-engine reference here would trip the S25 carryforward
 *   ``test_charter_integrity_dallas.py`` check at the T26.12 gate.
 *
 * Resilience invariant:
 *   Each quick-stats fetch lands in its own ``useQuery``. A single
 *   failing endpoint must NOT block the page render — the failed badge
 *   shows ``—`` and the other three keep their counts. We assert this
 *   here so the page never goes blank during a partial-API outage.
 */

vi.mock("@/lib/api/admin_feedback", () => ({
  listFlagged: vi.fn(),
  listVisits: vi.fn(),
}));

vi.mock("@/lib/api/listing_claims", () => ({
  listPendingClaims: vi.fn(),
}));

vi.mock("@/lib/api/assessments", () => ({
  listPendingAssessments: vi.fn(),
}));

vi.mock("@/lib/api/auth", () => ({
  useAccount: vi.fn(),
  useAccountRoles: vi.fn(),
}));

import { listFlagged, listVisits } from "@/lib/api/admin_feedback";
import { listPendingClaims } from "@/lib/api/listing_claims";
import { listPendingAssessments } from "@/lib/api/assessments";
import { useAccount, useAccountRoles } from "@/lib/api/auth";
import AdminLandingPage from "@/app/admin/page";

const mockedListFlagged = listFlagged as ReturnType<typeof vi.fn>;
const mockedListVisits = listVisits as ReturnType<typeof vi.fn>;
const mockedListClaims = listPendingClaims as ReturnType<typeof vi.fn>;
const mockedListAssessments =
  listPendingAssessments as ReturnType<typeof vi.fn>;
const mockedUseAccount = useAccount as unknown as ReturnType<typeof vi.fn>;
const mockedUseAccountRoles =
  useAccountRoles as unknown as ReturnType<typeof vi.fn>;

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <AdminLandingPage />
    </QueryClientProvider>,
  );
}

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

function resolveAllCountsHappy() {
  // 3 flagged resources
  mockedListFlagged.mockResolvedValue({
    items: [
      { id: 1, name: "A" },
      { id: 2, name: "B" },
      { id: 3, name: "C" },
    ],
  });
  // 7 unreviewed visits (limit=1; total reflects the full count)
  mockedListVisits.mockResolvedValue({
    items: [{ id: 99 }],
    total: 7,
    limit: 1,
    offset: 0,
  });
  // 5 pending claims
  mockedListClaims.mockResolvedValue([
    { claim_id: 1 },
    { claim_id: 2 },
    { claim_id: 3 },
    { claim_id: 4 },
    { claim_id: 5 },
  ]);
  // 2 pending assessments
  mockedListAssessments.mockResolvedValue([
    { version_id: 10 },
    { version_id: 11 },
  ]);
}

const SECTION_CARDS: ReadonlyArray<{
  testId: string;
  label: RegExp;
  href: string;
}> = [
  { testId: "section-card-assessments", label: /assessments/i, href: "/admin/assessments" },
  { testId: "section-card-listings", label: /listings/i, href: "/admin/listings" },
  { testId: "section-card-cities-dfw", label: /cities/i, href: "/admin/cities/dfw" },
  { testId: "section-card-resources", label: /resources/i, href: "/admin/resources" },
  { testId: "section-card-feedback", label: /feedback/i, href: "/admin/feedback" },
  { testId: "section-card-brightdata", label: /brightdata/i, href: "/admin/brightdata" },
];

describe("AdminLandingPage (/admin)", () => {
  beforeEach(() => {
    mockedListFlagged.mockReset();
    mockedListVisits.mockReset();
    mockedListClaims.mockReset();
    mockedListAssessments.mockReset();
    mockedUseAccount.mockReset();
    mockedUseAccountRoles.mockReset();
    signedInAdmin();
  });

  it("renders all six section cards with the expected labels", async () => {
    resolveAllCountsHappy();
    renderPage();

    for (const card of SECTION_CARDS) {
      // eslint-disable-next-line no-await-in-loop
      await waitFor(() => {
        expect(screen.getByTestId(card.testId)).toBeInTheDocument();
      });
      expect(screen.getByTestId(card.testId)).toHaveTextContent(card.label);
    }
  });

  it("each section card links to the correct admin sub-page (Next <Link>)", async () => {
    resolveAllCountsHappy();
    renderPage();

    await waitFor(() => {
      expect(
        screen.getByTestId("section-card-assessments"),
      ).toBeInTheDocument();
    });

    for (const card of SECTION_CARDS) {
      const cardEl = screen.getByTestId(card.testId);
      const link = within(cardEl).getByRole("link");
      expect(link).toHaveAttribute("href", card.href);
    }
  });

  it("renders quick-stats badges from the four count endpoints", async () => {
    resolveAllCountsHappy();
    renderPage();

    await waitFor(() => {
      expect(
        screen.getByTestId("quick-stat-flagged-resources"),
      ).toHaveTextContent(/3/);
    });
    expect(
      screen.getByTestId("quick-stat-unreviewed-visits"),
    ).toHaveTextContent(/7/);
    expect(
      screen.getByTestId("quick-stat-pending-claims"),
    ).toHaveTextContent(/5/);
    expect(
      screen.getByTestId("quick-stat-pending-assessments"),
    ).toHaveTextContent(/2/);

    // Each typed client is invoked exactly once for its badge.
    expect(mockedListFlagged).toHaveBeenCalledTimes(1);
    expect(mockedListVisits).toHaveBeenCalledTimes(1);
    expect(mockedListClaims).toHaveBeenCalledTimes(1);
    expect(mockedListAssessments).toHaveBeenCalledTimes(1);

    // ListVisits is queried as a 1-row probe with reviewed=false; the
    // `total` field carries the unreviewed count without paginating.
    expect(mockedListVisits).toHaveBeenCalledWith({
      reviewed: false,
      limit: 1,
    });
  });

  it("shows a loading placeholder while counts are in flight", () => {
    // Each client returns a never-resolving promise so the page stays
    // in the loading state for the duration of the assertion.
    mockedListFlagged.mockReturnValue(new Promise(() => {}));
    mockedListVisits.mockReturnValue(new Promise(() => {}));
    mockedListClaims.mockReturnValue(new Promise(() => {}));
    mockedListAssessments.mockReturnValue(new Promise(() => {}));

    renderPage();

    expect(
      screen.getByTestId("quick-stat-flagged-resources"),
    ).toHaveTextContent(/…|loading/i);
    expect(
      screen.getByTestId("quick-stat-unreviewed-visits"),
    ).toHaveTextContent(/…|loading/i);
    expect(
      screen.getByTestId("quick-stat-pending-claims"),
    ).toHaveTextContent(/…|loading/i);
    expect(
      screen.getByTestId("quick-stat-pending-assessments"),
    ).toHaveTextContent(/…|loading/i);

    // Section cards render immediately even while counts load — the
    // page must never be blank just because a probe is slow.
    expect(
      screen.getByTestId("section-card-assessments"),
    ).toBeInTheDocument();
  });

  it("falls back to '—' when a single count endpoint fails (rest still render)", async () => {
    // Flagged resources endpoint is broken; other three resolve cleanly.
    mockedListFlagged.mockRejectedValue(new Error("503 unavailable"));
    mockedListVisits.mockResolvedValue({
      items: [],
      total: 4,
      limit: 1,
      offset: 0,
    });
    mockedListClaims.mockResolvedValue([{ claim_id: 1 }, { claim_id: 2 }]);
    mockedListAssessments.mockResolvedValue([{ version_id: 99 }]);

    renderPage();

    // Healthy badges still show their counts.
    await waitFor(() => {
      expect(
        screen.getByTestId("quick-stat-unreviewed-visits"),
      ).toHaveTextContent(/4/);
    });
    expect(
      screen.getByTestId("quick-stat-pending-claims"),
    ).toHaveTextContent(/2/);
    expect(
      screen.getByTestId("quick-stat-pending-assessments"),
    ).toHaveTextContent(/1/);

    // Failed badge shows the documented em-dash fallback (NOT a blank
    // value, NOT a global error card — the page must keep rendering).
    await waitFor(() => {
      expect(
        screen.getByTestId("quick-stat-flagged-resources"),
      ).toHaveTextContent(/—/);
    });

    // All six section cards still render; the failure does not blank
    // the page.
    for (const card of SECTION_CARDS) {
      expect(screen.getByTestId(card.testId)).toBeInTheDocument();
    }
  });

  it("blocks non-admin reviewers via the strict RoleGate wrap", async () => {
    signedInNonAdmin();
    resolveAllCountsHappy();
    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/permission denied/i)).toBeInTheDocument();
    });
    expect(
      screen.queryByTestId("section-card-assessments"),
    ).not.toBeInTheDocument();
  });
});
