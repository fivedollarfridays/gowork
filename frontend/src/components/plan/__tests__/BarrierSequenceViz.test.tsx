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

  it("renders aria-labels on each step", () => {
    render(<BarrierSequenceViz sequence={SAMPLE_SEQUENCE} />);
    expect(screen.getByLabelText(/Step 1: Criminal Record/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Step 2: Childcare/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Step 3: Training/i)).toBeInTheDocument();
  });

  it("shows estimated weeks per step when available", () => {
    const withWeeks = {
      ...SAMPLE_SEQUENCE,
      steps: SAMPLE_SEQUENCE.steps.map((s, i) => ({
        ...s,
        estimated_weeks: [12, 6, 8][i],
      })),
      estimated_total_weeks: 26,
    };
    render(<BarrierSequenceViz sequence={withWeeks} />);
    expect(screen.getByText(/~12 weeks/i)).toBeInTheDocument();
    expect(screen.getByText(/~6 weeks/i)).toBeInTheDocument();
    expect(screen.getByText(/~8 weeks/i)).toBeInTheDocument();
  });

  it("shows total timeline estimate", () => {
    const withTotal = {
      ...SAMPLE_SEQUENCE,
      estimated_total_weeks: 24,
    };
    render(<BarrierSequenceViz sequence={withTotal} />);
    expect(screen.getByText(/~24 weeks/i)).toBeInTheDocument();
  });

  it("applies urgency color coding for legal category", () => {
    render(<BarrierSequenceViz sequence={SAMPLE_SEQUENCE} />);
    // Legal category (criminal_record) should have destructive/red styling
    const legalBadge = screen.getByText("legal");
    expect(legalBadge.className).toMatch(/destructive/);
  });

  it("renders cycle warning with aria-label", () => {
    const cycleData: BarrierSequenceData = {
      ...SAMPLE_SEQUENCE,
      has_cycles: true,
    };
    render(<BarrierSequenceViz sequence={cycleData} />);
    expect(screen.getByLabelText(/Cycle detected/i)).toBeInTheDocument();
  });
});
