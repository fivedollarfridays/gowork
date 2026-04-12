import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { SharedPlanView, type SharedPlanData } from "../SharedPlanView";

const SAMPLE_PLAN: SharedPlanData = {
  session_id: "test-123",
  created_at: "2026-04-11",
  barriers: ["credit", "transportation"],
  next_steps: [
    "Visit career center",
    "Update resume",
    "Apply for SNAP benefits",
  ],
  career_center_name: "Workforce Solutions for Tarrant County",
  career_center_phone: "817-413-4400",
};

function renderShared(plan: SharedPlanData | null = SAMPLE_PLAN) {
  return render(
    <TranslationProvider>
      <SharedPlanView plan={plan} />
    </TranslationProvider>,
  );
}

describe("SharedPlanView", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders shared plan heading", () => {
    renderShared();
    expect(screen.getByText(/shared action plan/i)).toBeInTheDocument();
  });

  it("renders next steps", () => {
    renderShared();
    expect(screen.getByText("Visit career center")).toBeInTheDocument();
    expect(screen.getByText("Update resume")).toBeInTheDocument();
    expect(screen.getByText("Apply for SNAP benefits")).toBeInTheDocument();
  });

  it("renders career center info", () => {
    renderShared();
    expect(screen.getByText(/Workforce Solutions/)).toBeInTheDocument();
    expect(screen.getByText("817-413-4400")).toBeInTheDocument();
  });

  it("renders barrier labels", () => {
    renderShared();
    expect(screen.getByText(/credit/i)).toBeInTheDocument();
    expect(screen.getByText(/transportation/i)).toBeInTheDocument();
  });

  it("shows invalid message when plan is null", () => {
    renderShared(null);
    expect(screen.getByText(/has expired or is invalid/i)).toBeInTheDocument();
  });

  it("renders in Spanish when locale is ES", () => {
    setLocale("es");
    renderShared();
    expect(screen.getByText(/plan de accion compartido/i)).toBeInTheDocument();
  });

  it("shows generation date", () => {
    renderShared();
    expect(screen.getByText(/2026-04-11/)).toBeInTheDocument();
  });
});
