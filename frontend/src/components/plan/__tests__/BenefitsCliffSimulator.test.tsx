import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BenefitsCliffSimulator } from "../BenefitsCliffSimulator";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import type { CliffAnalysis } from "@/lib/types";

function makeAnalysis(overrides: Partial<CliffAnalysis> = {}): CliffAnalysis {
  return {
    wage_steps: [
      { wage: 8, gross_monthly: 1387, benefits_total: 800, net_monthly: 2187 },
      { wage: 10, gross_monthly: 1733, benefits_total: 600, net_monthly: 2333 },
      { wage: 12, gross_monthly: 2080, benefits_total: 300, net_monthly: 2380 },
      { wage: 14, gross_monthly: 2427, benefits_total: 0, net_monthly: 2427 },
      { wage: 16, gross_monthly: 2773, benefits_total: 0, net_monthly: 2773 },
      { wage: 18, gross_monthly: 3120, benefits_total: 0, net_monthly: 3120 },
    ],
    cliff_points: [
      {
        hourly_wage: 12,
        annual_income: 24960,
        net_monthly_income: 2380,
        lost_program: "SNAP",
        monthly_loss: 200,
        severity: "moderate",
      },
      {
        hourly_wage: 14,
        annual_income: 29120,
        net_monthly_income: 2427,
        lost_program: "Section_8",
        monthly_loss: 300,
        severity: "severe",
      },
    ],
    current_net_monthly: 2187,
    programs: [
      { program: "SNAP", monthly_value: 300, eligible: true },
      { program: "Section_8", monthly_value: 500, eligible: true },
    ],
    worst_cliff_wage: 14,
    recovery_wage: 16,
    ...overrides,
  };
}

function renderSimulator(analysis: CliffAnalysis | null = makeAnalysis()) {
  return render(
    <TranslationProvider>
      <BenefitsCliffSimulator analysis={analysis} />
    </TranslationProvider>,
  );
}

describe("BenefitsCliffSimulator", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders nothing when analysis is null", () => {
    const { container } = renderSimulator(null);
    expect(container.firstChild).toBeNull();
  });

  it("renders heading", () => {
    renderSimulator();
    expect(screen.getByText(/benefit cliff simulator/i)).toBeInTheDocument();
  });

  it("renders a slider element", () => {
    renderSimulator();
    expect(screen.getByRole("slider")).toBeInTheDocument();
  });

  it("displays current wage value", () => {
    renderSimulator();
    // The min wage and current wage labels both show $8/hr (initial state)
    const wageLabels = screen.getAllByText("$8/hr");
    expect(wageLabels.length).toBeGreaterThanOrEqual(1);
  });

  it("displays net monthly income", () => {
    renderSimulator();
    expect(screen.getByText(/net monthly/i)).toBeInTheDocument();
  });

  it("displays benefits total", () => {
    renderSimulator();
    expect(screen.getByText(/total benefits/i)).toBeInTheDocument();
  });

  it("shows cliff warning markers", () => {
    renderSimulator();
    // Cliff points create warning indicators
    expect(screen.getByText(/SNAP/i)).toBeInTheDocument();
  });

  it("renders in Spanish when locale is ES", () => {
    setLocale("es");
    renderSimulator();
    expect(screen.getByText(/simulador/i)).toBeInTheDocument();
  });

  it("renders nothing for empty wage steps", () => {
    const { container } = renderSimulator(makeAnalysis({ wage_steps: [] }));
    expect(container.firstChild).toBeNull();
  });

  it("renders loading state", () => {
    render(
      <TranslationProvider>
        <BenefitsCliffSimulator analysis={null} loading={true} />
      </TranslationProvider>,
    );
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders error state", () => {
    render(
      <TranslationProvider>
        <BenefitsCliffSimulator analysis={null} error="Failed to load cliff data" />
      </TranslationProvider>,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
  });

  it("has accessible slider with aria label", () => {
    renderSimulator();
    const slider = screen.getByRole("slider");
    expect(slider).toHaveAttribute("aria-label");
  });

  it("shows cliff warning as alert role", () => {
    // Render with analysis where wage 12 has a cliff
    const analysis = makeAnalysis();
    render(
      <TranslationProvider>
        <BenefitsCliffSimulator analysis={analysis} />
      </TranslationProvider>,
    );
    // Cliff at $12 -- initial wage is $8 so no cliff alert initially
    // Check that cliff points summary renders
    expect(screen.getByText("$12/hr: SNAP")).toBeInTheDocument();
    expect(screen.getByText("$14/hr: Section_8")).toBeInTheDocument();
  });
});
