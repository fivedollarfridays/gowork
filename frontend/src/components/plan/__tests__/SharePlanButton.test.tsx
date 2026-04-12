import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { SharePlanButton } from "../SharePlanButton";

// Mock the API
vi.mock("@/lib/api", () => ({
  createShareLink: vi.fn(),
}));

describe("SharePlanButton", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock clipboard
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
  });

  it("renders share button", () => {
    render(<SharePlanButton sessionId="test-session" token="test-token" />);
    expect(screen.getByText(/Share Plan/i)).toBeInTheDocument();
  });

  it("calls createShareLink on click", async () => {
    const { createShareLink } = await import("@/lib/api");
    (createShareLink as ReturnType<typeof vi.fn>).mockResolvedValue({
      share_token: "abc123",
      url: "/shared/abc123",
    });

    render(<SharePlanButton sessionId="test-session" token="test-token" />);
    fireEvent.click(screen.getByText(/Share Plan/i));

    await waitFor(() => {
      expect(createShareLink).toHaveBeenCalledWith("test-session", "test-token");
    });
  });

  it("shows copied state after successful share", async () => {
    const { createShareLink } = await import("@/lib/api");
    (createShareLink as ReturnType<typeof vi.fn>).mockResolvedValue({
      share_token: "abc123",
      url: "/shared/abc123",
    });

    render(<SharePlanButton sessionId="test-session" token="test-token" />);
    fireEvent.click(screen.getByText(/Share Plan/i));

    await waitFor(() => {
      expect(screen.getByText(/Copied/i)).toBeInTheDocument();
    });
  });
});
