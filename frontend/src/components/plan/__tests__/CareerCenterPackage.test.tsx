import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { CareerCenterPrintLayout } from "../CareerCenterPackage";
import type { CareerCenterPackage } from "@/lib/types";

const basePackage: CareerCenterPackage = {
  staff_summary: {
    employment_goal: "Employment for unemployed resident",
    barrier_profile: ["credit", "transportation"],
    wioa_eligibility: {
      adult_program: true,
      adult_reasons: ["credit", "transportation"],
      supportive_services: true,
      ita_training: false,
      dislocated_worker: "needs_verification",
      confidence: "likely",
    },
    staff_next_steps: ["Visit Career Center", "Screen for WIOA"],
  },
  resident_plan: {
    document_checklist: [
      { label: "Government-issued photo ID", required: true },
      { label: "Social Security card", required: true },
      { label: "Resume (if available)", required: false },
    ],
    work_history: "Former CNA at Baptist Hospital",
    what_to_say: [
      "I'm here to get help finding employment.",
      "I may qualify for the WIOA Adult program.",
    ],
    what_to_expect: [
      "Initial intake and assessment (about 30 minutes)",
      "Review of your work history and goals",
    ],
    career_center: {
      name: "Montgomery Career Center",
      phone: "334-286-1746",
      address: "1060 East South Blvd, Montgomery, AL 36116",
      hours: "Mon-Fri 8am-5pm",
      transit_route: "Route 6",
    },
    programs: ["WIOA Adult Program", "WIOA Supportive Services"],
  },
  credit_pathway: null,
  generated_at: "2026-03-06T12:00:00Z",
};

const creditPathway = {
  blocking: ["Late payment on auto loan"],
  not_blocking: [],
  dispute_steps: ["Get free credit report", "File dispute with bureau"],
  free_resources: ["AnnualCreditReport.com"],
};

describe("CareerCenterPrintLayout", () => {
  it("renders staff summary with barrier profile", () => {
    render(<CareerCenterPrintLayout data={basePackage} />);
    expect(screen.getByText(/credit/)).toBeInTheDocument();
    expect(screen.getByText(/transportation/)).toBeInTheDocument();
  });

  it("renders WIOA eligibility checkmarks", () => {
    render(<CareerCenterPrintLayout data={basePackage} />);
    expect(screen.getByText(/✓ WIOA Adult Program/)).toBeInTheDocument();
    expect(screen.getByText(/✓ Supportive Services/)).toBeInTheDocument();
  });

  it("renders document checklist", () => {
    render(<CareerCenterPrintLayout data={basePackage} />);
    expect(screen.getByText(/Government-issued photo ID/)).toBeInTheDocument();
    expect(screen.getByText(/Social Security card/)).toBeInTheDocument();
  });

  it("renders what to say scripts", () => {
    render(<CareerCenterPrintLayout data={basePackage} />);
    expect(screen.getByText(/I'm here to get help/)).toBeInTheDocument();
    expect(screen.getByText(/WIOA Adult program/)).toBeInTheDocument();
  });

  it("renders career center info", () => {
    render(<CareerCenterPrintLayout data={basePackage} />);
    expect(screen.getByText(/Montgomery Career Center/)).toBeInTheDocument();
    expect(screen.getByText(/334-286-1746/)).toBeInTheDocument();
    expect(screen.getByText(/Mon-Fri 8am-5pm/)).toBeInTheDocument();
  });

  it("does not render credit section when null", () => {
    render(<CareerCenterPrintLayout data={basePackage} />);
    expect(screen.queryByText(/Credit Pathway/i)).not.toBeInTheDocument();
  });

  it("renders credit pathway when present", () => {
    const withCredit = { ...basePackage, credit_pathway: creditPathway };
    render(<CareerCenterPrintLayout data={withCredit} />);
    expect(screen.getByText(/Credit Pathway/i)).toBeInTheDocument();
    expect(screen.getByText(/Late payment on auto loan/)).toBeInTheDocument();
    expect(screen.getByText(/File dispute with bureau/)).toBeInTheDocument();
  });

  it("renders single-barrier profile without errors", () => {
    const singleBarrier = {
      ...basePackage,
      staff_summary: {
        ...basePackage.staff_summary,
        barrier_profile: ["childcare"],
        wioa_eligibility: null,
      },
    };
    render(<CareerCenterPrintLayout data={singleBarrier} />);
    expect(screen.getByText(/childcare/)).toBeInTheDocument();
  });

  it("has page break styles between sections", () => {
    const { container } = render(<CareerCenterPrintLayout data={basePackage} />);
    const pageBreaks = container.querySelectorAll("[data-page-break]");
    expect(pageBreaks.length).toBeGreaterThanOrEqual(1);
  });

  it("uses minimum 11pt font size", () => {
    const { container } = render(<CareerCenterPrintLayout data={basePackage} />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.fontSize).toBe("11pt");
  });
});
