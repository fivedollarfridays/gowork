import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ExplainSteps } from "@/components/barrier-intel/ExplainSteps";

const steps = [
  {
    step: 1,
    title: "Get childcare assistance",
    why: "Childcare is blocking your schedule.",
    barrierTags: ["CHILDCARE_EVENING"],
    evidence: ["Childcare Playbook", "Resource #3"],
  },
  {
    step: 2,
    title: "Apply for transportation aid",
    why: "You need a way to get to work.",
    barrierTags: ["TRANSPORTATION"],
    evidence: ["Transit Resource #1"],
  },
];

describe("ExplainSteps", () => {
  it("renders step titles", () => {
    render(<ExplainSteps steps={steps} />);
    expect(screen.getByText("Get childcare assistance")).toBeInTheDocument();
    expect(screen.getByText("Apply for transportation aid")).toBeInTheDocument();
  });

  it("renders barrier tags as badges", () => {
    render(<ExplainSteps steps={steps} />);
    expect(screen.getByText("CHILDCARE_EVENING")).toBeInTheDocument();
    expect(screen.getByText("TRANSPORTATION")).toBeInTheDocument();
  });

  it("reveals why section when toggled", async () => {
    render(<ExplainSteps steps={steps} />);
    const triggers = screen.getAllByText("Why this step?");
    fireEvent.click(triggers[0]);
    expect(screen.getByText("Childcare is blocking your schedule.")).toBeInTheDocument();
  });
});
