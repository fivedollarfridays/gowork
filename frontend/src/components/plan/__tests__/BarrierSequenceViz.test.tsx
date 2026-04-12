import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BarrierSequenceViz, type BarrierSequenceData } from "../BarrierSequenceViz";

const SAMPLE_SEQUENCE: BarrierSequenceData = {
  steps: [
    {
      order: 1,
      barrier_id: "criminal_record",
      barrier_name: "Criminal Record",
      category: "legal",
      playbook: "File for nondisclosure",
      unlocks: ["childcare"],
    },
    {
      order: 2,
      barrier_id: "childcare",
      barrier_name: "Childcare",
      category: "family",
      playbook: "Apply for childcare subsidy",
      unlocks: ["training"],
    },
    {
      order: 3,
      barrier_id: "training",
      barrier_name: "Training",
      category: "education",
      playbook: "Enroll in WIOA training",
      unlocks: [],
    },
  ],
  total_barriers: 3,
  has_cycles: false,
};

describe("BarrierSequenceViz", () => {
  it("renders all barrier steps", () => {
    render(<BarrierSequenceViz sequence={SAMPLE_SEQUENCE} />);
    expect(screen.getByText("Criminal Record")).toBeInTheDocument();
    expect(screen.getByText("Childcare")).toBeInTheDocument();
    expect(screen.getByText("Training")).toBeInTheDocument();
  });

  it("shows step numbers", () => {
    render(<BarrierSequenceViz sequence={SAMPLE_SEQUENCE} />);
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("shows unlock indicators", () => {
    render(<BarrierSequenceViz sequence={SAMPLE_SEQUENCE} />);
    // Criminal Record unlocks Childcare
    expect(screen.getByText(/Unlocks: Childcare/i)).toBeInTheDocument();
  });

  it("renders empty state for no barriers", () => {
    const empty: BarrierSequenceData = { steps: [], total_barriers: 0, has_cycles: false };
    render(<BarrierSequenceViz sequence={empty} />);
    expect(screen.getByText(/no barriers/i)).toBeInTheDocument();
  });

  it("shows heading", () => {
    render(<BarrierSequenceViz sequence={SAMPLE_SEQUENCE} />);
    expect(screen.getByText(/Barrier Resolution Order/i)).toBeInTheDocument();
  });

  it("shows playbook text for each step", () => {
    render(<BarrierSequenceViz sequence={SAMPLE_SEQUENCE} />);
    expect(screen.getByText(/File for nondisclosure/i)).toBeInTheDocument();
    expect(screen.getByText(/Apply for childcare subsidy/i)).toBeInTheDocument();
  });
});
