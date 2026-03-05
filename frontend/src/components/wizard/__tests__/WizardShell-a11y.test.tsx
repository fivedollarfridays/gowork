import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import React from "react";
import { WizardShell, type WizardStepConfig } from "../WizardShell";

function makeSteps(count: number): WizardStepConfig[] {
  return Array.from({ length: count }, (_, i) => ({
    title: `Step ${i + 1}`,
    icon: <span>icon{i}</span>,
    content: () => <div>Content for step {i + 1}</div>,
  }));
}

/** Find the Next/forward navigation button (may have aria-label override). */
function getNextButton() {
  // The Next button has aria-label "Go to step N: ..." when not last step
  const buttons = screen.getAllByRole("button");
  return buttons.find(
    (b) =>
      b.textContent?.includes("Next") ||
      b.getAttribute("aria-label")?.startsWith("Go to step")
  )!;
}

/** Find the Back button (may have aria-label override). */
function getBackButton() {
  const buttons = screen.getAllByRole("button");
  return buttons.find(
    (b) =>
      b.textContent?.includes("Back") &&
      !b.textContent?.includes("Next")
  )!;
}

describe("WizardShell a11y: aria-current on active step", () => {
  it("marks the current step indicator with aria-current='step'", () => {
    const steps = makeSteps(3);
    render(<WizardShell steps={steps} onComplete={vi.fn()} />);

    // Step 1 is active on mount
    const stepIndicators = screen.getAllByText(/^[1-3]$/);
    // The first indicator (showing "1") should have aria-current
    expect(stepIndicators[0].closest("[aria-current]")).toHaveAttribute(
      "aria-current",
      "step"
    );
  });

  it("does not mark non-current steps with aria-current", () => {
    const steps = makeSteps(3);
    render(<WizardShell steps={steps} onComplete={vi.fn()} />);

    // Steps 2 and 3 should NOT have aria-current
    const step2Text = screen.getByText("2");
    const step3Text = screen.getByText("3");
    expect(step2Text.closest("[aria-current]")).toBeNull();
    expect(step3Text.closest("[aria-current]")).toBeNull();
  });

  it("moves aria-current to the new step when navigating forward", () => {
    const steps = makeSteps(3);
    render(<WizardShell steps={steps} onComplete={vi.fn()} />);

    // Navigate to step 2
    fireEvent.click(getNextButton());

    // Now step 2 should have aria-current, step 1 should not
    const step2Text = screen.getByText("2");
    expect(step2Text.closest("[aria-current]")).toHaveAttribute(
      "aria-current",
      "step"
    );
    const step3Text = screen.getByText("3");
    expect(step3Text.closest("[aria-current]")).toBeNull();
  });
});

describe("WizardShell a11y: step content container", () => {
  it("step content container has tabIndex -1", () => {
    const steps = makeSteps(2);
    render(<WizardShell steps={steps} onComplete={vi.fn()} />);

    // The content container should have tabIndex={-1} for programmatic focus
    const content = screen.getByText("Content for step 1").closest(
      "[tabindex='-1']"
    );
    expect(content).not.toBeNull();
  });
});

describe("WizardShell a11y: focus management on step change", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("does not focus the step content on initial mount", () => {
    const steps = makeSteps(2);
    const { container } = render(
      <WizardShell steps={steps} onComplete={vi.fn()} />
    );

    act(() => {
      vi.runAllTimers();
    });

    // On initial mount, the step content container should NOT be the active element
    const contentContainer = container.querySelector("[tabindex='-1']");
    expect(document.activeElement).not.toBe(contentContainer);
  });

  it("focuses the step content container when navigating to the next step", () => {
    const steps = makeSteps(3);
    const { container } = render(
      <WizardShell steps={steps} onComplete={vi.fn()} />
    );

    // Navigate to step 2
    fireEvent.click(getNextButton());

    act(() => {
      vi.runAllTimers();
    });

    // The step content container should now be focused
    const contentContainer = container.querySelector("[tabindex='-1']");
    expect(document.activeElement).toBe(contentContainer);
  });

  it("focuses the step content container when navigating back", () => {
    const steps = makeSteps(3);
    const { container } = render(
      <WizardShell steps={steps} onComplete={vi.fn()} />
    );

    // Go forward then back
    fireEvent.click(getNextButton());
    act(() => {
      vi.runAllTimers();
    });

    fireEvent.click(getBackButton());
    act(() => {
      vi.runAllTimers();
    });

    const contentContainer = container.querySelector("[tabindex='-1']");
    expect(document.activeElement).toBe(contentContainer);
  });
});
