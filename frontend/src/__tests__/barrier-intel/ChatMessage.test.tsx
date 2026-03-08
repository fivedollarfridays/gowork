import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ChatMessage } from "@/components/barrier-intel/ChatMessage";

describe("ChatMessage", () => {
  it("renders user message with user role label", () => {
    render(<ChatMessage role="user" text="What should I do?" />);
    expect(screen.getByText("What should I do?")).toBeInTheDocument();
  });

  it("renders assistant message with assistant role label", () => {
    render(<ChatMessage role="assistant" text="Here are your next steps." />);
    expect(screen.getByText("Here are your next steps.")).toBeInTheDocument();
  });

  it("shows loading indicator when isStreaming is true", () => {
    render(<ChatMessage role="assistant" text="" isStreaming />);
    expect(screen.getByTestId("streaming-indicator")).toBeInTheDocument();
  });
});
