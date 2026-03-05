import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { WizardShell, type WizardStepConfig } from "../WizardShell";

function makeSteps(count: number): WizardStepConfig[] {
  return Array.from({ length: count }, (_, i) => ({
    title: `Step ${i + 1}`,
    icon: <span>{i + 1}</span>,
    content: () => <div>Content for step {i + 1}</div>,
    canAdvance: () => true,
  }));
}

describe("WizardShell ARIA labels", () => {
  it("Next button has aria-label referencing the next step title", () => {
    const steps = makeSteps(3);
    render(<WizardShell steps={steps} onComplete={vi.fn()} />);
    const nextBtn = screen.getByRole("button", { name: /go to step 2/i });
    expect(nextBtn).toBeInTheDocument();
    expect(nextBtn).toHaveAttribute("aria-label", "Go to step 2: Step 2");
  });

  it("Back button has aria-label referencing the previous step title when not on first step", async () => {
    const steps = makeSteps(3);
    render(<WizardShell steps={steps} onComplete={vi.fn()} />);
    const user = userEvent.setup();

    // Navigate to step 2
    const nextBtn = screen.getByRole("button", { name: /go to step 2/i });
    await user.click(nextBtn);

    // Back button should reference step 1
    const backBtn = screen.getByRole("button", { name: /go to step 1/i });
    expect(backBtn).toBeInTheDocument();
    expect(backBtn).toHaveAttribute("aria-label", "Go to step 1: Step 1");
  });

  it("Next button on last step does not have step aria-label (uses completeLabel)", async () => {
    const steps = makeSteps(2);
    render(<WizardShell steps={steps} onComplete={vi.fn()} />);
    const user = userEvent.setup();

    // Navigate to last step
    await user.click(screen.getByRole("button", { name: /go to step 2/i }));

    // The submit button should not have the step-specific aria-label
    const submitBtn = screen.getByRole("button", { name: /submit/i });
    expect(submitBtn).toBeInTheDocument();
    expect(submitBtn).not.toHaveAttribute("aria-label");
  });

  it("Back button on first step has no step aria-label", () => {
    const steps = makeSteps(3);
    render(<WizardShell steps={steps} onComplete={vi.fn()} />);

    // Back button exists but is invisible/disabled on first step — no aria-label needed
    const buttons = screen.getAllByRole("button");
    const backBtn = buttons.find((b) => b.textContent?.includes("Back"));
    expect(backBtn).toBeDefined();
    expect(backBtn).not.toHaveAttribute("aria-label");
  });
});
