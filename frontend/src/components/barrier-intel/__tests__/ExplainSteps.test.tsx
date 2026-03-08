import { render, screen, fireEvent } from "@testing-library/react";
import { ExplainSteps } from "../ExplainSteps";
import type { ExplainStep } from "@/lib/types";

const sampleSteps: ExplainStep[] = [
  { text: "Call GreenPath Financial", reasoning: "Credit counseling can help improve your score" },
  { text: "Check M-Transit Route 4", reasoning: "This route serves the career center" },
  { text: "Visit Alabama Career Center" },
];

describe("ExplainSteps", () => {
  it("renders nothing when steps is undefined", () => {
    const { container } = render(<ExplainSteps />);
    expect(container.innerHTML).toBe("");
  });

  it("renders nothing when steps is empty", () => {
    const { container } = render(<ExplainSteps steps={[]} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders numbered steps", () => {
    render(<ExplainSteps steps={sampleSteps} />);
    expect(screen.getByText("Call GreenPath Financial")).toBeInTheDocument();
    expect(screen.getByText("Check M-Transit Route 4")).toBeInTheDocument();
    expect(screen.getByText("Visit Alabama Career Center")).toBeInTheDocument();
  });

  it("shows step numbers", () => {
    render(<ExplainSteps steps={sampleSteps} />);
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("expands reasoning on click", () => {
    render(<ExplainSteps steps={sampleSteps} />);
    // Reasoning should not be visible initially
    expect(screen.queryByText("Credit counseling can help improve your score")).not.toBeInTheDocument();

    // Click "Why this step?" button
    const whyButtons = screen.getAllByRole("button", { name: /why this step/i });
    fireEvent.click(whyButtons[0]);

    expect(screen.getByText("Credit counseling can help improve your score")).toBeInTheDocument();
  });

  it("does not show why button when reasoning is absent", () => {
    render(<ExplainSteps steps={[{ text: "Simple step" }]} />);
    expect(screen.queryByRole("button", { name: /why this step/i })).not.toBeInTheDocument();
  });

  it("toggles reasoning closed on second click", () => {
    render(<ExplainSteps steps={sampleSteps} />);
    const whyButtons = screen.getAllByRole("button", { name: /why this step/i });
    fireEvent.click(whyButtons[0]);
    expect(screen.getByText("Credit counseling can help improve your score")).toBeInTheDocument();

    fireEvent.click(whyButtons[0]);
    expect(screen.queryByText("Credit counseling can help improve your score")).not.toBeInTheDocument();
  });

  it("is keyboard accessible", () => {
    render(<ExplainSteps steps={sampleSteps} />);
    const whyButtons = screen.getAllByRole("button", { name: /why this step/i });
    // Buttons should be focusable
    whyButtons[0].focus();
    expect(document.activeElement).toBe(whyButtons[0]);

    // Enter key should toggle
    fireEvent.keyDown(whyButtons[0], { key: "Enter" });
    fireEvent.click(whyButtons[0]);
    expect(screen.getByText("Credit counseling can help improve your score")).toBeInTheDocument();
  });
});
