import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

/**
 * Tests for `/admin/assessments/[versionId]` detail page (T23.7).
 *
 * Covers:
 *   - Auth guard redirect when useAccount() resolves to anonymous
 *   - Renders questions ordered by position
 *   - Action buttons submit (approve / reject / request_revision) and
 *     pass the comment textarea contents through to reviewAssessment()
 *   - Publish button visible only when status === "approved"
 */

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: pushMock }),
  useParams: () => ({ versionId: "11" }),
}));

vi.mock("@/lib/api/assessments", () => ({
  getAssessmentVersion: vi.fn(),
  reviewAssessment: vi.fn(),
  publishAssessment: vi.fn(),
}));
// The auth/role gate moved to the layout (T23.8). The detail page now
// reads only ``useAccountRoles`` to decide whether to surface the admin-
// only Publish button — anonymous handling is the layout's job.
vi.mock("@/lib/api/auth", () => ({
  useAccountRoles: vi.fn(),
}));

import {
  getAssessmentVersion,
  reviewAssessment,
  publishAssessment,
} from "@/lib/api/assessments";
import { useAccountRoles } from "@/lib/api/auth";
import AssessmentDetailPage from "@/app/admin/assessments/[versionId]/page";

const mockedGet = getAssessmentVersion as ReturnType<typeof vi.fn>;
const mockedReview = reviewAssessment as ReturnType<typeof vi.fn>;
const mockedPublish = publishAssessment as ReturnType<typeof vi.fn>;
const mockedUseAccountRoles =
  useAccountRoles as unknown as ReturnType<typeof vi.fn>;

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <AssessmentDetailPage />
    </QueryClientProvider>,
  );
}

const SAMPLE_VERSION = {
  version_id: 11,
  assessment_id: 1,
  version_number: 2,
  status: "in_review",
  drafted_by: 7,
  reviewed_by: null,
  approved_by: null,
  published_at: null,
  retired_at: null,
  created_at: "2026-05-01T00:00:00Z",
  questions: [
    { id: 100, position: 2, prompt: "Second prompt?", kind: "scale", rubric_json: {}, scoring_weight: 1.0 },
    { id: 101, position: 1, prompt: "First prompt?", kind: "scale", rubric_json: {}, scoring_weight: 1.0 },
  ],
};

/** Default reviewer signin — non-admin so publish button is hidden. */
function signedInReviewer() {
  mockedUseAccountRoles.mockReturnValue(["sme_reviewer"]);
}

/** Admin signin — publish button visible when status === "approved". */
function signedInAdmin() {
  mockedUseAccountRoles.mockReturnValue(["admin"]);
}

describe("AssessmentDetailPage (/admin/assessments/[versionId])", () => {
  beforeEach(() => {
    pushMock.mockReset();
    mockedGet.mockReset();
    mockedReview.mockReset();
    mockedPublish.mockReset();
    mockedUseAccountRoles.mockReset();
    // Default to a non-admin reviewer; tests that need admin override.
    signedInReviewer();
  });

  it("renders questions ordered by position", async () => {
    mockedGet.mockResolvedValueOnce(SAMPLE_VERSION);
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/First prompt\?/)).toBeInTheDocument();
    });
    const items = screen.getAllByRole("listitem");
    // First listed item should be position 1 ("First prompt?")
    expect(items[0]).toHaveTextContent(/First prompt\?/);
    expect(items[1]).toHaveTextContent(/Second prompt\?/);
  });

  it("submits an approve review with the comment textarea contents", async () => {
    signedInReviewer();
    mockedGet.mockResolvedValueOnce(SAMPLE_VERSION);
    mockedReview.mockResolvedValueOnce({ review_id: 42 });
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/First prompt\?/)).toBeInTheDocument();
    });
    await user.type(
      screen.getByLabelText(/comment/i),
      "looks great",
    );
    await user.click(screen.getByRole("button", { name: /approve/i }));
    await waitFor(() => {
      expect(mockedReview).toHaveBeenCalledWith(11, "approve", "looks great");
    });
  });

  it("submits a reject review", async () => {
    signedInReviewer();
    mockedGet.mockResolvedValueOnce(SAMPLE_VERSION);
    mockedReview.mockResolvedValueOnce({ review_id: 43 });
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/First prompt\?/)).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: /reject/i }));
    await waitFor(() => {
      expect(mockedReview).toHaveBeenCalledWith(11, "reject", null);
    });
  });

  it("submits a request_revision review", async () => {
    signedInReviewer();
    mockedGet.mockResolvedValueOnce(SAMPLE_VERSION);
    mockedReview.mockResolvedValueOnce({ review_id: 44 });
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/First prompt\?/)).toBeInTheDocument();
    });
    await user.click(
      screen.getByRole("button", { name: /request revision/i }),
    );
    await waitFor(() => {
      expect(mockedReview).toHaveBeenCalledWith(11, "request_revision", null);
    });
  });

  it("does not show publish button when status is in_review", async () => {
    signedInReviewer();
    mockedGet.mockResolvedValueOnce(SAMPLE_VERSION);
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/First prompt\?/)).toBeInTheDocument();
    });
    expect(
      screen.queryByRole("button", { name: /^publish/i }),
    ).not.toBeInTheDocument();
  });

  it("shows publish button when status is approved AND admin role held; calls publishAssessment", async () => {
    signedInAdmin();
    mockedGet.mockResolvedValueOnce({ ...SAMPLE_VERSION, status: "approved" });
    mockedPublish.mockResolvedValueOnce({
      assessment_id: 1,
      version_id: 11,
      version_number: 2,
      published_at: "2026-05-02T12:00:00Z",
      slug: "vocational-screen-v2",
      public_url: "/api/assessments/vocational-screen-v2",
    });
    const user = userEvent.setup();
    renderPage();
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /^publish/i }),
      ).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: /^publish/i }));
    await waitFor(() => {
      expect(mockedPublish).toHaveBeenCalledWith(11);
    });
  });

  it("hides publish button when status is approved but caller is non-admin", async () => {
    // Reviewer (sme_reviewer) on an approved version — backend would 403
    // a publish attempt, so the button should not render at all (T23.8).
    signedInReviewer();
    mockedGet.mockResolvedValueOnce({ ...SAMPLE_VERSION, status: "approved" });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/First prompt\?/)).toBeInTheDocument();
    });
    expect(
      screen.queryByRole("button", { name: /^publish/i }),
    ).not.toBeInTheDocument();
  });

  it("renders error state when fetch fails", async () => {
    signedInReviewer();
    mockedGet.mockRejectedValueOnce(new Error("nope"));
    renderPage();
    await waitFor(() => {
      expect(
        screen.getByText(/couldn|error|failed/i),
      ).toBeInTheDocument();
    });
  });
});
