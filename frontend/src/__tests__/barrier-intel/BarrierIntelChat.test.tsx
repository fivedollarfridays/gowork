import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BarrierIntelChat } from "@/components/barrier-intel/BarrierIntelChat";

const mockFetch = vi.fn();
global.fetch = mockFetch;

beforeEach(() => {
  mockFetch.mockReset();
});

describe("BarrierIntelChat", () => {
  it("renders suggested questions initially", () => {
    render(<BarrierIntelChat sessionId="sess-1" />);
    expect(screen.getByText("What should I do first to find a job?")).toBeInTheDocument();
  });

  it("renders the 'Explain this plan' button", () => {
    render(<BarrierIntelChat sessionId="sess-1" />);
    expect(screen.getByText("Explain this plan")).toBeInTheDocument();
  });

  it("renders the message input box", () => {
    render(<BarrierIntelChat sessionId="sess-1" />);
    expect(screen.getByPlaceholderText(/ask a question/i)).toBeInTheDocument();
  });

  it("submitting a question adds it to the message list", async () => {
    const tokenEvent = `data: ${JSON.stringify({ type: "token", text: "OK!" })}\n\n`;
    const doneEvent = `data: ${JSON.stringify({ type: "done", usage: {} })}\n\n`;

    const encoder = new TextEncoder();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      body: new ReadableStream({
        start(c) {
          c.enqueue(encoder.encode(tokenEvent + doneEvent));
          c.close();
        },
      }),
    });

    render(<BarrierIntelChat sessionId="sess-1" />);
    const input = screen.getByPlaceholderText(/ask a question/i);
    fireEvent.change(input, { target: { value: "What to do?" } });
    fireEvent.submit(input.closest("form")!);

    await waitFor(() => {
      expect(screen.getByText("What to do?")).toBeInTheDocument();
    });
  });

  it("shows error alert on fetch failure", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    render(<BarrierIntelChat sessionId="sess-1" />);
    const input = screen.getByPlaceholderText(/ask a question/i);
    fireEvent.change(input, { target: { value: "What to do?" } });
    fireEvent.submit(input.closest("form")!);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });
});
