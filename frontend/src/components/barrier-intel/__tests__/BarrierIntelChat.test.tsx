import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import { BarrierIntelChat } from "../BarrierIntelChat";
import { SuggestedQuestions } from "../SuggestedQuestions";
import { ChatMessage } from "../ChatMessage";

// Mock the streaming hook
const mockSendMessage = vi.fn();
vi.mock("@/hooks/useBarrierIntelStream", () => ({
  useBarrierIntelStream: () => ({
    messages: [],
    isStreaming: false,
    context: null,
    error: null,
    sendMessage: mockSendMessage,
  }),
}));

describe("BarrierIntelChat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns null when no sessionId", () => {
    const { container } = render(<BarrierIntelChat sessionId={null} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders mobile floating button initially", () => {
    render(<BarrierIntelChat sessionId="test-session" />);
    expect(screen.getByLabelText("Ask about your plan")).toBeInTheDocument();
  });

  it("opens chat panel when button clicked", () => {
    render(<BarrierIntelChat sessionId="test-session" />);
    fireEvent.click(screen.getByLabelText("Ask about your plan"));
    // Both desktop sidebar and mobile drawer render in jsdom
    expect(screen.getAllByText("Barrier Intelligence Assistant").length).toBeGreaterThan(0);
  });

  it("shows suggested questions when chat open and no messages", () => {
    render(<BarrierIntelChat sessionId="test-session" />);
    fireEvent.click(screen.getByLabelText("Ask about your plan"));
    expect(screen.getAllByText("What should I do first to find a job?").length).toBeGreaterThan(0);
  });

  it("has input field and send button", () => {
    render(<BarrierIntelChat sessionId="test-session" />);
    fireEvent.click(screen.getByLabelText("Ask about your plan"));
    expect(screen.getAllByPlaceholderText("Ask about your plan...").length).toBeGreaterThan(0);
  });

  it("closes chat panel on X button click", () => {
    render(<BarrierIntelChat sessionId="test-session" />);
    fireEvent.click(screen.getByLabelText("Ask about your plan"));
    // Both desktop and mobile render in jsdom; click the first close button
    fireEvent.click(screen.getAllByLabelText("Close chat")[0]);
    expect(screen.getByLabelText("Ask about your plan")).toBeInTheDocument();
  });
});

describe("SuggestedQuestions", () => {
  it("renders three suggestion chips", () => {
    const onSelect = vi.fn();
    render(<SuggestedQuestions onSelect={onSelect} />);
    expect(screen.getAllByRole("button")).toHaveLength(3);
  });

  it("calls onSelect when chip clicked", () => {
    const onSelect = vi.fn();
    render(<SuggestedQuestions onSelect={onSelect} />);
    fireEvent.click(screen.getByText("What should I do first to find a job?"));
    expect(onSelect).toHaveBeenCalledWith("What should I do first to find a job?");
  });

  it("disables chips when disabled prop set", () => {
    render(<SuggestedQuestions onSelect={vi.fn()} disabled />);
    const buttons = screen.getAllByRole("button");
    buttons.forEach((btn) => expect(btn).toBeDisabled());
  });
});

describe("ChatMessage", () => {
  it("renders user message aligned right", () => {
    render(<ChatMessage message={{ role: "user", content: "Hello" }} />);
    expect(screen.getByText("Hello")).toBeInTheDocument();
  });

  it("renders assistant message aligned left", () => {
    render(<ChatMessage message={{ role: "assistant", content: "I can help" }} />);
    expect(screen.getByText("I can help")).toBeInTheDocument();
  });

  it("shows loading indicator when streaming and empty", () => {
    const { container } = render(
      <ChatMessage message={{ role: "assistant", content: "" }} isStreaming />,
    );
    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
  });
});
