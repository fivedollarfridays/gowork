import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MondayMorning } from "../MondayMorning";
import type { ReEntryPlan, UserProfile } from "@/lib/types";
import { AvailableHours, BarrierType, EmploymentStatus } from "@/lib/types";

const basePlan: ReEntryPlan = {
  plan_id: "plan-001",
  session_id: "sess-abc",
  resident_summary: null,
  barriers: [],
  job_matches: [],
  strong_matches: [],
  possible_matches: [],
  after_repair: [],
  immediate_next_steps: ["Visit career center"],
  credit_readiness_score: null,
  eligible_now: [],
  eligible_after_repair: [],
  wioa_eligibility: null,
  job_readiness: null,
};

const baseProfile: UserProfile = {
  session_id: "sess-abc",
  zip_code: "36104",
  employment_status: EmploymentStatus.UNEMPLOYED,
  barrier_count: 0,
  primary_barriers: [],
  barrier_severity: "low",
  needs_credit_assessment: false,
  transit_dependent: false,
  schedule_type: AvailableHours.DAYTIME,
  work_history: "",
  target_industries: [],
};

function renderMondayMorning(overrides?: Partial<Parameters<typeof MondayMorning>[0]>) {
  return render(
    <MondayMorning
      plan={basePlan}
      profile={baseProfile}
      {...overrides}
    />
  );
}

describe("MondayMorning dynamic heading", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("says 'tomorrow morning' on a weekday (Mon-Thu)", () => {
    // Wednesday March 4, 2026
    vi.setSystemTime(new Date(2026, 2, 4, 10, 0, 0));
    renderMondayMorning();
    expect(screen.getByText(/tomorrow morning/i)).toBeInTheDocument();
  });

  it("says 'Monday morning' on a Friday", () => {
    // Friday March 6, 2026
    vi.setSystemTime(new Date(2026, 2, 6, 10, 0, 0));
    renderMondayMorning();
    expect(screen.getByText(/Monday morning/i)).toBeInTheDocument();
  });

  it("says 'Monday morning' on a Saturday", () => {
    // Saturday March 7, 2026
    vi.setSystemTime(new Date(2026, 2, 7, 10, 0, 0));
    renderMondayMorning();
    expect(screen.getByText(/Monday morning/i)).toBeInTheDocument();
  });

  it("says 'tomorrow morning' on a Sunday", () => {
    // Sunday March 8, 2026
    vi.setSystemTime(new Date(2026, 2, 8, 10, 0, 0));
    renderMondayMorning();
    expect(screen.getByText(/tomorrow morning/i)).toBeInTheDocument();
  });
});

describe("MondayMorning clickable phone numbers", () => {
  const planWithResource: ReEntryPlan = {
    ...basePlan,
    barriers: [
      {
        type: BarrierType.CREDIT,
        severity: "medium",
        title: "Credit Barrier",
        timeline_days: null,
        actions: [],
        transit_matches: [],
        resources: [
          {
            id: 1,
            name: "Montgomery Career Center",
            address: "100 Main St, Montgomery, AL",
            phone: "(334) 555-1234",
            url: null,
            category: "career_center",
            subcategory: null,
            eligibility: null,
            services: null,
            notes: null,
          },
        ],
      },
    ],
  };

  it("renders phone as tel: link, not as plain text in detail", () => {
    renderMondayMorning({ plan: planWithResource });

    // The phone number should be rendered as a clickable tel: link
    const phoneLinks = screen.getAllByRole("link").filter(
      (link) => link.getAttribute("href")?.startsWith("tel:")
    );
    expect(phoneLinks.length).toBeGreaterThanOrEqual(1);

    // The step detail should NOT contain the raw phone number as plain text
    // It should say "Call ahead" without embedding the number
    const callAheadText = screen.queryByText(/Call ahead: \(334\)/);
    expect(callAheadText).not.toBeInTheDocument();
  });

  it("shows phone number in step card detail area", () => {
    renderMondayMorning({ plan: planWithResource });
    // The phone should appear as text content within the card
    expect(screen.getByText("(334) 555-1234")).toBeInTheDocument();
  });
});

describe("MondayMorning fixed step cards", () => {
  it("renders Career Center step with phone link", () => {
    renderMondayMorning();

    expect(screen.getByText(/Visit the Career Center/)).toBeInTheDocument();
    const phoneLinks = screen.getAllByRole("link").filter(
      (link) => link.getAttribute("href")?.startsWith("tel:")
    );
    expect(phoneLinks.length).toBeGreaterThanOrEqual(1);
  });

  it("renders Job Matches and Barriers steps", () => {
    renderMondayMorning();

    expect(screen.getByText(/Review Your Job Matches/)).toBeInTheDocument();
    expect(screen.getByText(/No Barriers Identified/)).toBeInTheDocument();
  });
});

describe("MondayMorning map links", () => {
  const planWithAddress: ReEntryPlan = {
    ...basePlan,
    barriers: [
      {
        type: BarrierType.CREDIT,
        severity: "medium",
        title: "Credit Barrier",
        timeline_days: null,
        actions: [],
        transit_matches: [],
        resources: [
          {
            id: 1,
            name: "Montgomery Career Center",
            address: "100 Main St, Montgomery, AL",
            phone: null,
            url: null,
            category: "career_center",
            subcategory: null,
            eligibility: null,
            services: null,
            notes: null,
          },
        ],
      },
    ],
  };

  it("uses Google Maps search URL for address links", () => {
    renderMondayMorning({ plan: planWithAddress });

    const mapLinks = screen.getAllByRole("link").filter(
      (link) => link.getAttribute("href")?.includes("google.com/maps")
    );
    expect(mapLinks.length).toBeGreaterThanOrEqual(1);
    expect(mapLinks[0].getAttribute("href")).toContain("google.com/maps/search");
  });

  it("encodes resource address in map URL", () => {
    renderMondayMorning({ plan: planWithAddress });

    const mapLinks = screen.getAllByRole("link").filter(
      (link) => link.getAttribute("href")?.includes("google.com/maps")
    );
    // Find the link that contains the resource address (not the CAREER_CENTER address)
    const resourceMapLink = mapLinks.find((link) =>
      link.getAttribute("href")?.includes(encodeURIComponent("100 Main St"))
    );
    expect(resourceMapLink).toBeDefined();
    expect(resourceMapLink!.getAttribute("href")).toContain(
      encodeURIComponent("100 Main St, Montgomery, AL")
    );
  });
});

