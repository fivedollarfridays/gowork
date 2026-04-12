import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { TimelinePhaseCard } from "../TimelinePhaseCard";
import type { TimelinePhase } from "@/lib/types";

// Mock useCityConfig for Alabama (default)
vi.mock("@/hooks/useCityConfig", () => ({
  useCityConfig: () => ({
    name: "Montgomery",
    state: "AL",
    location: "Montgomery, AL",
    zip_ranges: ["36101-36199"],
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

describe("TimelinePhaseCard AL regression", () => {
  it("renders job application link to Alabama JobLink", () => {
    const phase = makePhase({
      actions: [
        {
          title: "Apply for Healthcare Aide",
          category: "job_application",
          priority: "high",
        },
      ],
    });

    render(<TimelinePhaseCard phase={phase} dateRange="Apr 11 - Apr 18" defaultOpen />);

    const link = screen.getByRole("link", { name: /apply/i });
    expect(link).toHaveAttribute("href", "https://joblink.alabama.gov/");
  });

  it("renders career center link to Montgomery address", () => {
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
    expect(link.getAttribute("href")).toContain("Montgomery");
  });

  it("renders housing link to HAMD for AL", () => {
    const phase = makePhase({
      actions: [
        {
          title: "Apply for housing",
          category: "housing",
          priority: "medium",
        },
      ],
    });

    render(<TimelinePhaseCard phase={phase} dateRange="Apr 11 - Apr 18" defaultOpen />);

    const link = screen.getByRole("link", { name: /apply/i });
    expect(link).toHaveAttribute("href", "https://www.hamd.org/");
  });

  it("renders childcare link to Alabama DHR for AL", () => {
    const phase = makePhase({
      actions: [
        {
          title: "Apply for childcare",
          category: "childcare",
          priority: "medium",
        },
      ],
    });

    render(<TimelinePhaseCard phase={phase} dateRange="Apr 11 - Apr 18" defaultOpen />);

    const link = screen.getByRole("link", { name: /apply/i });
    expect(link.getAttribute("href")).toContain("dhr.alabama.gov");
  });

  it("renders criminal record link to Legal Services Alabama for AL", () => {
    const phase = makePhase({
      actions: [
        {
          title: "Contact legal services about expungement",
          category: "criminal_record",
          priority: "high",
        },
      ],
    });

    render(<TimelinePhaseCard phase={phase} dateRange="Apr 11 - Apr 18" defaultOpen />);

    const link = screen.getByRole("link", { name: /contact/i });
    expect(link.getAttribute("href")).toContain("legalservicesalabama");
  });
});
