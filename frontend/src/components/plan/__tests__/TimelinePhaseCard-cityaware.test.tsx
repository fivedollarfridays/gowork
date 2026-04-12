import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TimelinePhaseCard } from "../TimelinePhaseCard";
import type { TimelinePhase } from "@/lib/types";

// Mock useCityConfig to control state
vi.mock("@/hooks/useCityConfig", () => ({
  useCityConfig: () => ({
    name: "Fort Worth",
    state: "TX",
    location: "Fort Worth, TX",
    zip_ranges: ["76101-76199"],
    loading: false,
  }),
}));

function makePhase(overrides: Partial<TimelinePhase> = {}): TimelinePhase {
  return {
    phase_id: "phase_1",
    label: "Week 1",
    start_day: 0,
    end_day: 7,
    actions: [],
    ...overrides,
  };
}

describe("TimelinePhaseCard city-aware links (TX)", () => {
  it("renders job application link to WorkInTexas", async () => {
    const user = userEvent.setup();
    const phase = makePhase({
      actions: [
        {
          title: "Apply for Warehouse Associate at Amazon",
          category: "job_application",
          priority: "high",
        },
      ],
    });

    render(<TimelinePhaseCard phase={phase} dateRange="Apr 11 - Apr 18" defaultOpen />);

    // The action should have an "Apply" link
    const link = screen.getByRole("link", { name: /apply/i });
    expect(link).toHaveAttribute("href", "https://www.workintexas.com/");
  });

  it("renders career center link to Fort Worth address", async () => {
    const phase = makePhase({
      actions: [
        {
          title: "Visit the Career Center",
          category: "career_center",
          priority: "high",
        },
      ],
    });

    render(<TimelinePhaseCard phase={phase} dateRange="Apr 11 - Apr 18" defaultOpen />);

    const link = screen.getByRole("link", { name: /visit/i });
    // Should link to Fort Worth Workforce Solutions address via Google Maps
    expect(link.getAttribute("href")).toContain("google.com/maps");
    expect(link.getAttribute("href")).toContain("Fort%20Worth");
  });

  it("renders housing link to Fort Worth Housing Solutions", () => {
    const phase = makePhase({
      actions: [
        {
          title: "Apply for housing assistance",
          category: "housing",
          priority: "medium",
        },
      ],
    });

    render(<TimelinePhaseCard phase={phase} dateRange="Apr 11 - Apr 18" defaultOpen />);

    const link = screen.getByRole("link", { name: /apply/i });
    expect(link).toHaveAttribute("href", "https://www.fwhs.org/");
  });

  it("renders childcare link to Texas TWC", () => {
    const phase = makePhase({
      actions: [
        {
          title: "Apply for childcare assistance",
          category: "childcare",
          priority: "medium",
        },
      ],
    });

    render(<TimelinePhaseCard phase={phase} dateRange="Apr 11 - Apr 18" defaultOpen />);

    const link = screen.getByRole("link", { name: /apply/i });
    expect(link.getAttribute("href")).toContain("twc.texas.gov");
  });

  it("renders criminal record link to Legal Aid of NW Texas", () => {
    const phase = makePhase({
      actions: [
        {
          title: "Contact legal services for expunction review",
          category: "criminal_record",
          priority: "high",
        },
      ],
    });

    render(<TimelinePhaseCard phase={phase} dateRange="Apr 11 - Apr 18" defaultOpen />);

    const link = screen.getByRole("link", { name: /contact/i });
    expect(link).toHaveAttribute("href", "https://www.lanwt.org/");
  });

  it("renders benefits link to YourTexasBenefits", () => {
    const phase = makePhase({
      actions: [
        {
          title: "Apply for SNAP benefits",
          category: "benefits_enrollment",
          priority: "high",
        },
      ],
    });

    render(<TimelinePhaseCard phase={phase} dateRange="Apr 11 - Apr 18" defaultOpen />);

    const link = screen.getByRole("link", { name: /apply/i });
    expect(link.getAttribute("href")).toContain("yourtexasbenefits");
  });
});
