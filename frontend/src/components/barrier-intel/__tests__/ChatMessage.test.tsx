import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ChatMessage } from "../ChatMessage";
import type { ChatMessage as ChatMessageType } from "@/lib/types";

describe("ChatMessage", () => {
  it("renders basic user message", () => {
    const msg: ChatMessageType = { role: "user", content: "Hello" };
    render(<ChatMessage message={msg} />);
    expect(screen.getByText("Hello")).toBeInTheDocument();
  });

  it("renders basic assistant message", () => {
    const msg: ChatMessageType = { role: "assistant", content: "Here is your plan." };
    render(<ChatMessage message={msg} />);
    expect(screen.getByText("Here is your plan.")).toBeInTheDocument();
  });

  it("renders ExplainSteps when steps present", () => {
    const msg: ChatMessageType = {
      role: "assistant",
      content: "Follow these steps:",
      steps: [
        { text: "Call GreenPath Financial", reasoning: "Credit counseling helps" },
        { text: "Visit career center" },
      ],
    };
    render(<ChatMessage message={msg} />);
    expect(screen.getByText("Call GreenPath Financial")).toBeInTheDocument();
    expect(screen.getByText("Visit career center")).toBeInTheDocument();
  });

  it("renders EvidenceChips when evidence present", () => {
    const msg: ChatMessageType = {
      role: "assistant",
      content: "Based on these resources:",
      evidence: [
        { name: "GreenPath Financial", resource_id: 14 },
        { name: "M-Transit" },
      ],
    };
    render(<ChatMessage message={msg} />);
    expect(screen.getByText("GreenPath Financial")).toBeInTheDocument();
    expect(screen.getByText("M-Transit")).toBeInTheDocument();
  });

  it("renders disclaimer when present", () => {
    const msg: ChatMessageType = {
      role: "assistant",
      content: "Visit Springfield Job Center for help.",
      disclaimer: "Unverified: Springfield Job Center",
    };
    render(<ChatMessage message={msg} />);
    expect(screen.getByText(/Unverified: Springfield Job Center/)).toBeInTheDocument();
  });

  it("does not render explainability when data absent", () => {
    const msg: ChatMessageType = { role: "assistant", content: "Simple response." };
    const { container } = render(<ChatMessage message={msg} />);
    // Should not have steps or evidence sections
    expect(screen.queryByText("Sources")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /why this step/i })).not.toBeInTheDocument();
  });

  it("shows streaming indicator when streaming and empty", () => {
    const msg: ChatMessageType = { role: "assistant", content: "" };
    const { container } = render(<ChatMessage message={msg} isStreaming />);
    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
  });
});
