import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BarrierCardView } from "../BarrierCardView";
import { BarrierType } from "@/lib/types";
import type { BarrierCard } from "@/lib/types";

// Mock api module
vi.mock("@/lib/api", () => ({
  submitResourceFeedback: vi.fn(() => Promise.resolve({ success: true, resource_id: 1, helpful: true })),
}));

const SESSION_ID = "test-session-123";
const TOKEN = "test-token-abc";

const barrier: BarrierCard = {
  type: BarrierType.TRANSPORTATION,
  severity: "high",
  title: "Transportation Access",
  timeline_days: null,
  actions: ["Review M-Transit routes"],
  resources: [
    {
      id: 1,
      name: "Montgomery Career Center",
      category: "career_center",
      subcategory: null,
      address: "1060 East South Boulevard",
      phone: "334-286-1746",
      url: null,
      eligibility: null,
      services: null,
      notes: null,
    },
  ],
  transit_matches: [],
};

beforeEach(() => {
  sessionStorage.clear();
  vi.clearAllMocks();
});

describe("Resource feedback buttons", () => {
  it("renders thumbs up and thumbs down buttons for each resource", () => {
    render(<BarrierCardView barrier={barrier} sessionId={SESSION_ID} token={TOKEN} />);

    expect(screen.getByRole("button", { name: "Mark as helpful" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mark as not helpful" })).toBeInTheDocument();
  });

  it("toggles visual state on click (optimistic)", async () => {
    render(<BarrierCardView barrier={barrier} sessionId={SESSION_ID} token={TOKEN} />);

    const helpfulBtn = screen.getByRole("button", { name: "Mark as helpful" });
    fireEvent.click(helpfulBtn);

    // Button should visually change after click
    await waitFor(() => {
      expect(helpfulBtn).toHaveAttribute("data-active", "true");
    });
  });

  it("fires API call with correct payload on click", async () => {
    const { submitResourceFeedback } = await import("@/lib/api");

    render(<BarrierCardView barrier={barrier} sessionId={SESSION_ID} token={TOKEN} />);

    const helpfulBtn = screen.getByRole("button", { name: "Mark as helpful" });
    fireEvent.click(helpfulBtn);

    await waitFor(() => {
      expect(submitResourceFeedback).toHaveBeenCalledWith({
        resource_id: 1,
        session_id: SESSION_ID,
        helpful: true,
        token: TOKEN,
      });
    });
  });

  it("persists state to sessionStorage", async () => {
    render(<BarrierCardView barrier={barrier} sessionId={SESSION_ID} token={TOKEN} />);

    const helpfulBtn = screen.getByRole("button", { name: "Mark as helpful" });
    fireEvent.click(helpfulBtn);

    await waitFor(() => {
      const stored = sessionStorage.getItem(`feedback_${SESSION_ID}_1`);
      expect(stored).toBe("true");
    });
  });

  it("re-tapping same button deselects (neutral)", async () => {
    render(<BarrierCardView barrier={barrier} sessionId={SESSION_ID} token={TOKEN} />);

    const helpfulBtn = screen.getByRole("button", { name: "Mark as helpful" });

    // Click to select
    fireEvent.click(helpfulBtn);
    await waitFor(() => {
      expect(helpfulBtn).toHaveAttribute("data-active", "true");
    });

    // Click again to deselect
    fireEvent.click(helpfulBtn);
    await waitFor(() => {
      expect(helpfulBtn).not.toHaveAttribute("data-active", "true");
    });
  });

  it("switching vote clears the other button", async () => {
    render(<BarrierCardView barrier={barrier} sessionId={SESSION_ID} token={TOKEN} />);

    const helpfulBtn = screen.getByRole("button", { name: "Mark as helpful" });
    const notHelpfulBtn = screen.getByRole("button", { name: "Mark as not helpful" });

    // Click helpful
    fireEvent.click(helpfulBtn);
    await waitFor(() => {
      expect(helpfulBtn).toHaveAttribute("data-active", "true");
    });

    // Click not helpful — should switch
    fireEvent.click(notHelpfulBtn);
    await waitFor(() => {
      expect(notHelpfulBtn).toHaveAttribute("data-active", "true");
      expect(helpfulBtn).not.toHaveAttribute("data-active", "true");
    });
  });

  it("restores state from sessionStorage on mount", () => {
    sessionStorage.setItem(`feedback_${SESSION_ID}_1`, "true");

    render(<BarrierCardView barrier={barrier} sessionId={SESSION_ID} token={TOKEN} />);

    const helpfulBtn = screen.getByRole("button", { name: "Mark as helpful" });
    expect(helpfulBtn).toHaveAttribute("data-active", "true");
  });

  it("has aria-labels for accessibility", () => {
    render(<BarrierCardView barrier={barrier} sessionId={SESSION_ID} token={TOKEN} />);

    expect(screen.getByRole("button", { name: "Mark as helpful" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mark as not helpful" })).toBeInTheDocument();
  });

  it("does not render feedback buttons without sessionId", () => {
    render(<BarrierCardView barrier={barrier} />);

    expect(screen.queryByRole("button", { name: "Mark as helpful" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Mark as not helpful" })).not.toBeInTheDocument();
  });
});
