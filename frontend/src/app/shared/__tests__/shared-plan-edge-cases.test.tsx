import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { SharedPlanView, type SharedPlanData } from "../SharedPlanView";

function renderShared(plan: SharedPlanData | null) {
  return render(
    <TranslationProvider>
      <SharedPlanView plan={plan} />
    </TranslationProvider>,
  );
}

describe("SharedPlanView edge cases", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders expired/invalid message when plan is null", () => {
    renderShared(null);
    expect(screen.getByText(/has expired or is invalid/i)).toBeInTheDocument();
  });

  it("renders plan with no barriers (count = 0)", () => {
    renderShared({
      created_at: "2026-04-11",
      barriers_count: 0,
      next_steps: ["Contact career center"],
      career_center_name: "Test Center",
      career_center_phone: "555-0100",
    });
    expect(screen.getByText("Test Center")).toBeInTheDocument();
    expect(screen.getByText("Contact career center")).toBeInTheDocument();
    // T13 stage-2 P1-1: copy is now i18n-driven (share.barriersZero).
    expect(screen.getByText(/no focus areas identified/i)).toBeInTheDocument();
  });

  it("renders plan with no next steps", () => {
    renderShared({
      created_at: "2026-04-11",
      barriers_count: 1,
      next_steps: [],
      career_center_name: "Test Center",
      career_center_phone: "555-0100",
    });
    expect(screen.getByText("Test Center")).toBeInTheDocument();
    // T13 stage-2 P1-1: copy is now i18n-driven (share.barriersOne).
    expect(screen.getByText(/1 focus area identified/i)).toBeInTheDocument();
  });

  it("renders plan with many barriers (count only, no slug leak)", () => {
    renderShared({
      created_at: "2026-04-11",
      barriers_count: 7,
      next_steps: ["Step 1"],
      career_center_name: "All Barriers Center",
      career_center_phone: "555-0200",
    });
    // Renders the count, not the underlying slugs (T13.71 P1)
    // T13 stage-2 P1-1: copy is now i18n-driven (share.barriersMany).
    expect(screen.getByText(/7 focus areas identified/i)).toBeInTheDocument();
    expect(screen.queryByText(/^criminal record$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^credit$/i)).not.toBeInTheDocument();
  });

  it("shows phone number as clickable link", () => {
    renderShared({
      created_at: "2026-04-11",
      barriers_count: 0,
      next_steps: [],
      career_center_name: "Phone Center",
      career_center_phone: "817-413-4400",
    });
    const phoneLink = screen.getByText("817-413-4400");
    expect(phoneLink.closest("a")).toHaveAttribute("href", "tel:8174134400");
  });

  it("hides phone link when career_center_phone is empty (T13.72)", () => {
    renderShared({
      created_at: "2026-04-11",
      barriers_count: 0,
      next_steps: ["Step 1"],
      career_center_name: "",
      career_center_phone: "",
    });
    // No broken tel: link, no card title for an absent center
    expect(screen.queryByText(/career center/i)).not.toBeInTheDocument();
  });

  it("renders in Spanish when locale is ES", () => {
    setLocale("es");
    renderShared({
      created_at: "2026-04-11",
      barriers_count: 1,
      next_steps: ["Visitar centro de empleo"],
      career_center_name: "Workforce Solutions",
      career_center_phone: "555-0300",
    });
    expect(screen.getByText(/plan de accion compartido/i)).toBeInTheDocument();
    // T13 stage-2 P1-1: focus-areas + career-center titles + barrier
    // count are now i18n. Verify the ES strings actually render.
    expect(screen.getByText(/areas de enfoque/i)).toBeInTheDocument();
    expect(screen.getByText(/centro profesional/i)).toBeInTheDocument();
    expect(
      screen.getByText(/1 area de enfoque identificada/i),
    ).toBeInTheDocument();
  });

  it("renders Spanish expired message when plan is null", () => {
    setLocale("es");
    renderShared(null);
    expect(screen.getByText(/ha expirado o no es v/i)).toBeInTheDocument();
  });
});
