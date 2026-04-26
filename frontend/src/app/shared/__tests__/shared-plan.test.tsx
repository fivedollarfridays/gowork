import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { SharedPlanView, type SharedPlanData } from "../SharedPlanView";

const SAMPLE_PLAN: SharedPlanData = {
  // T13.71 P1 contract: no session_id, no raw barriers slugs.
  created_at: "2026-04-11",
  barriers_count: 2,
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

  it("renders a non-PII focus-areas count instead of raw barrier slugs", () => {
    renderShared();
    // T13.71 P1: the public payload exposes a count, not the slug list.
    // T13 stage-2 P1-1: copy is now i18n-driven (share.barriersMany).
    expect(screen.getByText(/2 focus areas identified/i)).toBeInTheDocument();
    // Ensure no raw slugs leak through the UI
    expect(screen.queryByText(/^credit$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^transportation$/i)).not.toBeInTheDocument();
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

  it("shows generation date formatted (no raw ISO microseconds)", () => {
    renderShared();
    // The component now formats the timestamp via toLocaleDateString — we just
    // assert a 2026 year appears and the raw ISO string does NOT.
    expect(screen.getByText(/2026/)).toBeInTheDocument();
    expect(screen.queryByText(/T\d{2}:\d{2}:\d{2}/)).not.toBeInTheDocument();
  });
});
