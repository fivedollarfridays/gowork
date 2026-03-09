import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BenefitsCliffChart } from "../BenefitsCliffChart";
import type { CliffAnalysis } from "@/lib/types";

function makeAnalysis(overrides: Partial<CliffAnalysis> = {}): CliffAnalysis {
  return {
    wage_steps: [
      { wage: 10, gross_monthly: 1733, benefits_total: 500, net_monthly: 2100 },
      { wage: 12, gross_monthly: 2080, benefits_total: 300, net_monthly: 2200 },
      { wage: 14, gross_monthly: 2427, benefits_total: 0, net_monthly: 2100 },
      { wage: 16, gross_monthly: 2773, benefits_total: 0, net_monthly: 2400 },
    ],
    cliff_points: [
      {
        hourly_wage: 14,
        annual_income: 29120,
        net_monthly_income: 2100,
        lost_program: "Section_8",
        monthly_loss: 300,
        severity: "severe",
      },
    ],
    current_net_monthly: 1800,
    programs: [{ program: "Section_8", monthly_value: 500, eligible: true }],
    worst_cliff_wage: 14,
    recovery_wage: 16,
    ...overrides,
  };
}

describe("BenefitsCliffChart", () => {
  it("renders nothing when analysis is null", () => {
    const { container } = render(
      <BenefitsCliffChart analysis={null} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders chart section heading", () => {
    render(<BenefitsCliffChart analysis={makeAnalysis()} />);
    expect(screen.getByText(/benefits cliff/i)).toBeInTheDocument();
  });

  it("provides accessible text summary", () => {
    render(<BenefitsCliffChart analysis={makeAnalysis()} />);
    expect(screen.getByText(/biggest cliff/i)).toBeInTheDocument();
    expect(screen.getByText(/\$14/)).toBeInTheDocument();
  });

  it("shows recovery wage in summary", () => {
    render(
      <BenefitsCliffChart
        analysis={makeAnalysis({ recovery_wage: 16 })}
      />,
    );
    expect(screen.getByText(/\$16/)).toBeInTheDocument();
  });

  it("shows no-cliff message when no cliff points", () => {
    render(
      <BenefitsCliffChart
        analysis={makeAnalysis({
          cliff_points: [],
          worst_cliff_wage: null,
          recovery_wage: null,
        })}
      />,
    );
    expect(screen.getByText(/no significant.*cliff/i)).toBeInTheDocument();
  });

  it("renders chart container with aria-label", () => {
    render(<BenefitsCliffChart analysis={makeAnalysis()} />);
    const chart = screen.getByRole("img");
    expect(chart).toHaveAttribute("aria-label");
  });
});
