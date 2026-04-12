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

  it("shows error state when share fails", async () => {
    const { createShareLink } = await import("@/lib/api");
    (createShareLink as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("Network error"),
    );

    render(<SharePlanButton sessionId="test-session" token="test-token" />);
    fireEvent.click(screen.getByText(/Share Plan/i));

    await waitFor(() => {
      expect(screen.getByText(/Failed/i)).toBeInTheDocument();
    });
  });

  it("disables button during loading", async () => {
    const { createShareLink } = await import("@/lib/api");
    let resolveShare: (val: { share_token: string; url: string }) => void;
    (createShareLink as ReturnType<typeof vi.fn>).mockReturnValue(
      new Promise((resolve) => { resolveShare = resolve; }),
    );

    render(<SharePlanButton sessionId="test-session" token="test-token" />);
    fireEvent.click(screen.getByText(/Share Plan/i));

    await waitFor(() => {
      const btn = screen.getByRole("button");
      expect(btn).toBeDisabled();
    });

    // Resolve to clean up
    resolveShare!({ share_token: "abc", url: "/shared/abc" });
  });

  it("copies full URL to clipboard", async () => {
    const { createShareLink } = await import("@/lib/api");
    (createShareLink as ReturnType<typeof vi.fn>).mockResolvedValue({
      share_token: "xyz789",
      url: "/shared/xyz789",
    });

    render(<SharePlanButton sessionId="test-session" token="test-token" />);
    fireEvent.click(screen.getByText(/Share Plan/i));

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
        expect.stringContaining("/shared/xyz789"),
      );
    });
  });
});
