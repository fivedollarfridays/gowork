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
    expect(screen.getByText(/15/)).toBeInTheDocument();
    expect(screen.getByText(/Fair-chance employer pool/i)).toBeInTheDocument();
  });
});
