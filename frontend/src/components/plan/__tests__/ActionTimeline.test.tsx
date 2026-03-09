import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ActionTimeline } from "../ActionTimeline";
import type { ActionPlan, TimelinePhase, ActionItem } from "@/lib/types";

function makeAction(overrides: Partial<ActionItem> = {}): ActionItem {
  return {
    category: "career_center",
    title: "Visit Montgomery Career Center",
    detail: "Bring photo ID and resume",
    priority: 1,
    source_module: "career_center",
    resource_name: "Montgomery Career Center",
    resource_phone: "(334) 286-1746",
    resource_address: null,
    ...overrides,
  };
}

function makePhase(overrides: Partial<TimelinePhase> = {}): TimelinePhase {
  return {
    phase_id: "week_1_2",
    label: "Week 1-2",
    start_day: 0,
    end_day: 14,
    actions: [makeAction()],
    ...overrides,
  };
}

function makePlan(overrides: Partial<ActionPlan> = {}): ActionPlan {
  return {
    assessment_date: "2026-03-09",
    phases: [
      makePhase({ phase_id: "week_1_2", label: "Week 1-2", start_day: 0, end_day: 14 }),
      makePhase({
        phase_id: "month_1",
        label: "Month 1",
        start_day: 14,
        end_day: 30,
        actions: [makeAction({ category: "job_application", title: "Apply to top 3 jobs", resource_name: null, resource_phone: null })],
      }),
      makePhase({
        phase_id: "month_2_3",
        label: "Month 2-3",
        start_day: 30,
        end_day: 90,
        actions: [makeAction({ category: "credit_repair", title: "Follow up on disputes" })],
      }),
      makePhase({
        phase_id: "month_3_6",
        label: "Month 3-6",
        start_day: 90,
        end_day: 180,
        actions: [makeAction({ category: "training", title: "Complete CNA training" })],
      }),
      makePhase({
        phase_id: "month_6_12",
        label: "Month 6-12",
        start_day: 180,
        end_day: 365,
        actions: [makeAction({ category: "benefits_enrollment", title: "Review benefits transition" })],
      }),
    ],
    total_actions: 5,
    ...overrides,
  };
}

describe("ActionTimeline", () => {
  it("renders nothing when actionPlan is null", () => {
    const { container } = render(<ActionTimeline actionPlan={null} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders nothing when actionPlan is undefined", () => {
    const { container } = render(<ActionTimeline actionPlan={undefined} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders all 5 phase headings", () => {
    render(<ActionTimeline actionPlan={makePlan()} />);
    expect(screen.getByText("Week 1-2")).toBeInTheDocument();
    expect(screen.getByText("Month 1")).toBeInTheDocument();
    expect(screen.getByText("Month 2-3")).toBeInTheDocument();
    expect(screen.getByText("Month 3-6")).toBeInTheDocument();
    expect(screen.getByText("Month 6-12")).toBeInTheDocument();
  });

  it("shows date ranges calculated from assessment date", () => {
    render(<ActionTimeline actionPlan={makePlan()} />);
    // Week 1-2: assessment_date 2026-03-09 + 0 days to +14 days = Mar 9 - Mar 23
    expect(screen.getByText("Mar 9 - Mar 23")).toBeInTheDocument();
  });

  it("first phase is expanded by default (actions visible)", () => {
    render(<ActionTimeline actionPlan={makePlan()} />);
    expect(screen.getByText("Visit Montgomery Career Center")).toBeInTheDocument();
  });

  it("other phases are collapsed by default", () => {
    render(<ActionTimeline actionPlan={makePlan()} />);
    // Month 1 action should not be visible (collapsed)
    expect(screen.queryByText("Apply to top 3 jobs")).not.toBeInTheDocument();
  });

  it("clicking a collapsed phase header expands it", async () => {
    const user = userEvent.setup();
    render(<ActionTimeline actionPlan={makePlan()} />);
    // Month 1 phase should be collapsed
    expect(screen.queryByText("Apply to top 3 jobs")).not.toBeInTheDocument();
    // Click the Month 1 phase toggle
    const month1Toggle = screen.getByRole("button", { name: /Month 1/i });
    await user.click(month1Toggle);
    expect(screen.getByText("Apply to top 3 jobs")).toBeInTheDocument();
  });

  it("shows action count badge per phase", () => {
    render(<ActionTimeline actionPlan={makePlan()} />);
    // Each phase has 1 action, so we should see "1 action" badges
    const badges = screen.getAllByText("1 action");
    expect(badges.length).toBeGreaterThanOrEqual(5);
  });

  it("shows action items with titles", () => {
    render(<ActionTimeline actionPlan={makePlan()} />);
    // First phase is expanded, so we can see its action title
    expect(screen.getByText("Visit Montgomery Career Center")).toBeInTheDocument();
  });

  it("shows resource phone when available", () => {
    render(<ActionTimeline actionPlan={makePlan()} />);
    // First phase is expanded and has a resource phone
    const phoneLink = screen.getByRole("link", { name: "(334) 286-1746" });
    expect(phoneLink).toHaveAttribute("href", "tel:3342861746");
  });

  it("shows resource name when available", () => {
    render(<ActionTimeline actionPlan={makePlan()} />);
    expect(screen.getByText("Montgomery Career Center")).toBeInTheDocument();
  });

  it("has accessible section landmark", () => {
    render(<ActionTimeline actionPlan={makePlan()} />);
    const section = screen.getByRole("region", { name: /action plan timeline/i });
    expect(section).toBeInTheDocument();
  });

  it("phase headers have aria-expanded attribute", () => {
    render(<ActionTimeline actionPlan={makePlan()} />);
    // First phase expanded
    const firstToggle = screen.getByRole("button", { name: /Week 1-2/i });
    expect(firstToggle).toHaveAttribute("aria-expanded", "true");
    // Second phase collapsed
    const secondToggle = screen.getByRole("button", { name: /Month 1/i });
    expect(secondToggle).toHaveAttribute("aria-expanded", "false");
  });

  it("skips phases with 0 actions", () => {
    const plan = makePlan({
      phases: [
        makePhase({ phase_id: "week_1_2", label: "Week 1-2", actions: [makeAction()] }),
        makePhase({ phase_id: "month_1", label: "Month 1", actions: [] }),
      ],
      total_actions: 1,
    });
    render(<ActionTimeline actionPlan={plan} />);
    expect(screen.getByText("Week 1-2")).toBeInTheDocument();
    expect(screen.queryByText("Month 1")).not.toBeInTheDocument();
  });

  it("renders section heading", () => {
    render(<ActionTimeline actionPlan={makePlan()} />);
    expect(screen.getByText("Your Action Plan Timeline")).toBeInTheDocument();
  });

  it("shows action detail when present", () => {
    render(<ActionTimeline actionPlan={makePlan()} />);
    expect(screen.getByText("Bring photo ID and resume")).toBeInTheDocument();
  });

  it("shows plural action count for phases with multiple actions", () => {
    const plan = makePlan({
      phases: [
        makePhase({
          phase_id: "week_1_2",
          label: "Week 1-2",
          actions: [makeAction(), makeAction({ title: "Register for WIOA", category: "training" })],
        }),
      ],
      total_actions: 2,
    });
    render(<ActionTimeline actionPlan={plan} />);
    expect(screen.getByText("2 actions")).toBeInTheDocument();
  });

  it("renders checkboxes when checklist prop is provided", () => {
    const plan = makePlan({
      phases: [makePhase({ phase_id: "week_1_2", label: "Week 1-2", actions: [makeAction()] })],
      total_actions: 1,
    });
    render(<ActionTimeline actionPlan={plan} checklist={{}} onToggle={() => {}} />);
    expect(screen.getByRole("checkbox")).toBeInTheDocument();
  });

  it("checkbox reflects completed state from checklist", () => {
    const plan = makePlan({
      phases: [makePhase({ phase_id: "week_1_2", label: "Week 1-2", actions: [makeAction()] })],
      total_actions: 1,
    });
    render(
      <ActionTimeline actionPlan={plan} checklist={{ "week_1_2:0": true }} onToggle={() => {}} />,
    );
    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toBeChecked();
  });

  it("renders resource_address as clickable Google Maps link", () => {
    const plan = makePlan({
      phases: [
        makePhase({
          phase_id: "week_1_2",
          label: "Week 1-2",
          actions: [makeAction({ resource_address: "1060 East South Blvd, Montgomery, AL 36116" })],
        }),
      ],
      total_actions: 1,
    });
    render(<ActionTimeline actionPlan={plan} />);
    const addressLink = screen.getByRole("link", { name: /1060 East South Blvd/i });
    expect(addressLink).toHaveAttribute(
      "href",
      expect.stringContaining("google.com/maps"),
    );
  });

  it("auto-links phone numbers in detail text", () => {
    const plan = makePlan({
      phases: [
        makePhase({
          phase_id: "week_1_2",
          label: "Week 1-2",
          actions: [makeAction({ detail: "1-800-550-1961", resource_name: null, resource_phone: null, resource_address: null })],
        }),
      ],
      total_actions: 1,
    });
    render(<ActionTimeline actionPlan={plan} />);
    const phoneLink = screen.getByRole("link", { name: "1-800-550-1961" });
    expect(phoneLink).toHaveAttribute("href", "tel:18005501961");
  });

  it("auto-links phone embedded in detail text with surrounding words", () => {
    const plan = makePlan({
      phases: [
        makePhase({
          phase_id: "week_1_2",
          label: "Week 1-2",
          actions: [makeAction({ detail: "Free consultation: 1-866-456-4995", resource_name: null, resource_phone: null, resource_address: null })],
        }),
      ],
      total_actions: 1,
    });
    render(<ActionTimeline actionPlan={plan} />);
    expect(screen.getByText(/Free consultation:/)).toBeInTheDocument();
    const phoneLink = screen.getByRole("link", { name: "1-866-456-4995" });
    expect(phoneLink).toHaveAttribute("href", "tel:18664564995");
  });

  it("auto-links multiple phone numbers in same detail text", () => {
    const plan = makePlan({
      phases: [
        makePhase({
          phase_id: "week_1_2",
          label: "Week 1-2",
          actions: [makeAction({
            detail: "Call (334) 286-1746 or (334) 832-9060 for info",
            resource_name: null,
            resource_phone: null,
            resource_address: null,
          })],
        }),
      ],
      total_actions: 1,
    });
    render(<ActionTimeline actionPlan={plan} />);
    const links = screen.getAllByRole("link");
    const phoneLinks = links.filter(
      (l) => l.getAttribute("href")?.startsWith("tel:"),
    );
    expect(phoneLinks).toHaveLength(2);
    expect(phoneLinks[0]).toHaveTextContent("(334) 286-1746");
    expect(phoneLinks[1]).toHaveTextContent("(334) 832-9060");
  });

  it("calls onToggle with action key when checkbox clicked", async () => {
    const user = userEvent.setup();
    const onToggle = vi.fn();
    const plan = makePlan({
      phases: [makePhase({ phase_id: "week_1_2", label: "Week 1-2", actions: [makeAction()] })],
      total_actions: 1,
    });
    render(<ActionTimeline actionPlan={plan} checklist={{}} onToggle={onToggle} />);
    await user.click(screen.getByRole("checkbox"));
    expect(onToggle).toHaveBeenCalledWith("week_1_2:0", true);
  });
});
