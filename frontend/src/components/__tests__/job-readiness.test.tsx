import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { JobReadinessResults } from "../plan/JobReadinessResults";
import { CareerPathway } from "../plan/CareerPathway";
import type { JobReadinessResult } from "@/lib/types";

function makeResult(overrides: Partial<JobReadinessResult> = {}): JobReadinessResult {
  return {
    overall_score: 65,
    readiness_band: "ready",
    factors: [
      { name: "Skills Match", weight: 0.3, score: 70, detail: "Resume skills vs job requirements" },
      { name: "Industry Alignment", weight: 0.25, score: 60, detail: "Target industries vs available jobs" },
      { name: "Barrier Resolution", weight: 0.2, score: 50, detail: "Employment barriers remaining" },
      { name: "Work Experience", weight: 0.15, score: 80, detail: "Resume quality and certifications" },
      { name: "Credit Readiness", weight: 0.1, score: 100, detail: "Credit status for employment" },
    ],
    pathway: [
      { step_number: 1, action: "Build job-relevant skills", resource: "Career Center", timeline_days: 30, completed: false },
      { step_number: 2, action: "Address barriers", resource: "See barrier cards", timeline_days: 60, completed: false },
    ],
    estimated_days_to_ready: 90,
    summary: "You're ready for many jobs in your target industries.",
    ...overrides,
  };
}

describe("JobReadinessResults", () => {
  it("displays overall score", () => {
    render(<JobReadinessResults result={makeResult()} />);
    expect(screen.getAllByText("65/100").length).toBeGreaterThanOrEqual(1);
  });

  it("displays readiness band badge", () => {
    render(<JobReadinessResults result={makeResult()} />);
    expect(screen.getByText("ready")).toBeInTheDocument();
  });

  it("displays all 5 factors", () => {
    render(<JobReadinessResults result={makeResult()} />);
    expect(screen.getByText(/Skills Match/)).toBeInTheDocument();
    expect(screen.getByText(/Industry Alignment/)).toBeInTheDocument();
    expect(screen.getByText(/Barrier Resolution/)).toBeInTheDocument();
    expect(screen.getByText(/Work Experience/)).toBeInTheDocument();
    expect(screen.getByText(/Credit Readiness/)).toBeInTheDocument();
  });

  it("displays factor weights", () => {
    render(<JobReadinessResults result={makeResult()} />);
    expect(screen.getByText("(30%)")).toBeInTheDocument();
    expect(screen.getByText("(25%)")).toBeInTheDocument();
    expect(screen.getByText("(20%)")).toBeInTheDocument();
    expect(screen.getByText("(15%)")).toBeInTheDocument();
    expect(screen.getByText("(10%)")).toBeInTheDocument();
  });

  it("displays summary text", () => {
    render(<JobReadinessResults result={makeResult()} />);
    expect(screen.getByText(/ready for many jobs/i)).toBeInTheDocument();
  });

  it("renders not_ready band with appropriate styling", () => {
    render(<JobReadinessResults result={makeResult({ readiness_band: "not_ready", overall_score: 25 })} />);
    expect(screen.getByText("not ready")).toBeInTheDocument();
  });

  it("renders strong band", () => {
    render(<JobReadinessResults result={makeResult({ readiness_band: "strong", overall_score: 90 })} />);
    expect(screen.getByText("strong")).toBeInTheDocument();
  });

  it("renders pathway steps", () => {
    render(<JobReadinessResults result={makeResult()} />);
    expect(screen.getByText("Build job-relevant skills")).toBeInTheDocument();
    expect(screen.getByText("Address barriers")).toBeInTheDocument();
  });
});

describe("CareerPathway", () => {
  it("renders nothing when no steps", () => {
    const { container } = render(<CareerPathway steps={[]} estimatedDays={0} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders step numbers and actions", () => {
    const steps = [
      { step_number: 1, action: "Build skills", resource: "Career Center", timeline_days: 30, completed: false },
      { step_number: 2, action: "Update resume", resource: "Workshop", timeline_days: 7, completed: false },
    ];
    render(<CareerPathway steps={steps} estimatedDays={37} />);

    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("Build skills")).toBeInTheDocument();
    expect(screen.getByText("Update resume")).toBeInTheDocument();
  });

  it("displays estimated time", () => {
    const steps = [
      { step_number: 1, action: "Do something", resource: "Resource", timeline_days: 90, completed: false },
    ];
    render(<CareerPathway steps={steps} estimatedDays={90} />);
    expect(screen.getByText(/estimated time to ready.*~3 months/i)).toBeInTheDocument();
  });
});
