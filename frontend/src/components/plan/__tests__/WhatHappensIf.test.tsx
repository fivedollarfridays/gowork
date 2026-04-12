import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { WhatHappensIf } from "../WhatHappensIf";

const BARRIERS = ["criminal_record", "childcare", "credit"];

describe("WhatHappensIf", () => {
  it("renders toggle switches for each barrier", () => {
    render(<WhatHappensIf barriers={BARRIERS} onSimulate={vi.fn()} />);
    expect(screen.getByText(/Criminal Record/i)).toBeInTheDocument();
    expect(screen.getByText(/Childcare/i)).toBeInTheDocument();
    expect(screen.getByText(/Credit/i)).toBeInTheDocument();
  });

  it("shows heading", () => {
    render(<WhatHappensIf barriers={BARRIERS} onSimulate={vi.fn()} />);
    expect(screen.getByText(/What Happens If/i)).toBeInTheDocument();
  });

  it("calls onSimulate when a barrier is toggled", () => {
    const onSimulate = vi.fn();
    render(<WhatHappensIf barriers={BARRIERS} onSimulate={onSimulate} />);
    const toggle = screen.getAllByRole("switch")[0];
    fireEvent.click(toggle);
    expect(onSimulate).toHaveBeenCalled();
  });

  it("renders empty state for no barriers", () => {
    render(<WhatHappensIf barriers={[]} onSimulate={vi.fn()} />);
    expect(screen.getByText(/no barriers/i)).toBeInTheDocument();
  });

  it("shows impact summary when simulation results provided", () => {
    const results = {
      barriers_resolved: ["criminal_record"],
      barriers_remaining: ["childcare", "credit"],
      unlocked_barriers: ["childcare"],
      jobs_unlocked_estimate: 15,
      benefits_unlocked: ["Fair-chance employer pool"],
      sequence_after: { steps: [], total_barriers: 2, has_cycles: false },
    };
    render(
      <WhatHappensIf barriers={BARRIERS} onSimulate={vi.fn()} simulationResults={results} />,
    );
    expect(screen.getAllByText(/\+15/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Fair-chance employer pool/i)).toBeInTheDocument();
  });

  it("shows summary sentence with jobs and benefits count", () => {
    const results = {
      barriers_resolved: ["criminal_record", "credit", "childcare"],
      barriers_remaining: [],
      unlocked_barriers: [],
      jobs_unlocked_estimate: 33,
      benefits_unlocked: ["Fair-chance pool", "Credit counseling", "Childcare subsidy"],
      sequence_after: { steps: [], total_barriers: 0, has_cycles: false },
    };
    render(
      <WhatHappensIf barriers={BARRIERS} onSimulate={vi.fn()} simulationResults={results} />,
    );
    expect(screen.getByText(/Resolving these 3 barriers/i)).toBeInTheDocument();
  });

  it("renders reset button when barriers are toggled", () => {
    render(<WhatHappensIf barriers={BARRIERS} onSimulate={vi.fn()} />);
    // Toggle one barrier
    const toggle = screen.getAllByRole("switch")[0];
    fireEvent.click(toggle);
    // Reset button should appear
    expect(screen.getByRole("button", { name: /Reset/i })).toBeInTheDocument();
  });

  it("reset button clears all toggled barriers", () => {
    const onSimulate = vi.fn();
    render(<WhatHappensIf barriers={BARRIERS} onSimulate={onSimulate} />);
    // Toggle two barriers
    const toggles = screen.getAllByRole("switch");
    fireEvent.click(toggles[0]);
    fireEvent.click(toggles[1]);
    // Click reset
    const resetBtn = screen.getByRole("button", { name: /Reset/i });
    fireEvent.click(resetBtn);
    // All switches should be unchecked
    const switches = screen.getAllByRole("switch");
    switches.forEach((s) => {
      expect(s.getAttribute("aria-checked")).toBe("false");
    });
  });

  it("shows loading state when isLoading prop is true", () => {
    render(
      <WhatHappensIf barriers={BARRIERS} onSimulate={vi.fn()} isLoading={true} />,
    );
    expect(screen.getByText(/Calculating/i)).toBeInTheDocument();
  });
});
