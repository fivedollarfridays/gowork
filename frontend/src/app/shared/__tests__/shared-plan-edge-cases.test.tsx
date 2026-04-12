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

  it("renders plan with no barriers", () => {
    renderShared({
      session_id: "no-barriers",
      created_at: "2026-04-11",
      barriers: [],
      next_steps: ["Contact career center"],
      career_center_name: "Test Center",
      career_center_phone: "555-0100",
    });
    expect(screen.getByText("Test Center")).toBeInTheDocument();
    expect(screen.getByText("Contact career center")).toBeInTheDocument();
  });

  it("renders plan with no next steps", () => {
    renderShared({
      session_id: "no-steps",
      created_at: "2026-04-11",
      barriers: ["credit"],
      next_steps: [],
      career_center_name: "Test Center",
      career_center_phone: "555-0100",
    });
    expect(screen.getByText("Test Center")).toBeInTheDocument();
  });

  it("renders plan with many barriers", () => {
    renderShared({
      session_id: "many-barriers",
      created_at: "2026-04-11",
      barriers: [
        "credit",
        "transportation",
        "childcare",
        "housing",
        "health",
        "training",
        "criminal_record",
      ],
      next_steps: ["Step 1"],
      career_center_name: "All Barriers Center",
      career_center_phone: "555-0200",
    });
    // All barrier badges should render
    expect(screen.getByText(/credit/i)).toBeInTheDocument();
    expect(screen.getByText(/transportation/i)).toBeInTheDocument();
    expect(screen.getByText(/criminal record/i)).toBeInTheDocument();
  });

  it("shows phone number as clickable link", () => {
    renderShared({
      session_id: "phone-test",
      created_at: "2026-04-11",
      barriers: [],
      next_steps: [],
      career_center_name: "Phone Center",
      career_center_phone: "817-413-4400",
    });
    const phoneLink = screen.getByText("817-413-4400");
    expect(phoneLink.closest("a")).toHaveAttribute("href", "tel:8174134400");
  });

  it("renders in Spanish when locale is ES", () => {
    setLocale("es");
    renderShared({
      session_id: "es-test",
      created_at: "2026-04-11",
      barriers: ["credit"],
      next_steps: ["Visitar centro de empleo"],
      career_center_name: "Workforce Solutions",
      career_center_phone: "555-0300",
    });
    expect(screen.getByText(/plan de accion compartido/i)).toBeInTheDocument();
  });

  it("renders Spanish expired message when plan is null", () => {
    setLocale("es");
    renderShared(null);
    expect(screen.getByText(/ha expirado o no es v/i)).toBeInTheDocument();
  });
});
