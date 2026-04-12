import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ProgressTracker, type ProgressStep } from "../ProgressTracker";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";

const SAMPLE_STEPS: ProgressStep[] = [
  { key: "step-1", label: "Visit career center", completed: false },
  { key: "step-2", label: "Update resume", completed: true },
  { key: "step-3", label: "Apply for SNAP", completed: false },
];

function renderTracker(
  steps = SAMPLE_STEPS,
  onToggle = vi.fn(),
) {
  return render(
    <TranslationProvider>
      <ProgressTracker steps={steps} onToggle={onToggle} />
    </TranslationProvider>,
  );
}

describe("ProgressTracker", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders heading", () => {
    renderTracker();
    expect(screen.getByText(/your progress/i)).toBeInTheDocument();
  });

  it("renders all step labels", () => {
    renderTracker();
    expect(screen.getByText("Visit career center")).toBeInTheDocument();
    expect(screen.getByText("Update resume")).toBeInTheDocument();
    expect(screen.getByText("Apply for SNAP")).toBeInTheDocument();
  });

  it("shows correct completion count", () => {
    renderTracker();
    // 1 completed, 2 remaining
    expect(screen.getByText(/1 completed/i)).toBeInTheDocument();
    expect(screen.getByText(/2 remaining/i)).toBeInTheDocument();
  });

  it("calls onToggle when checkbox is clicked", async () => {
    const onToggle = vi.fn();
    const user = userEvent.setup();
    renderTracker(SAMPLE_STEPS, onToggle);

    const checkboxes = screen.getAllByRole("checkbox");
    await user.click(checkboxes[0]); // Toggle first unchecked step
    expect(onToggle).toHaveBeenCalledWith("step-1", true);
  });

  it("calls onToggle with false when unchecking", async () => {
    const onToggle = vi.fn();
    const user = userEvent.setup();
    renderTracker(SAMPLE_STEPS, onToggle);

    const checkboxes = screen.getAllByRole("checkbox");
    // The second checkbox (step-2) is already checked
    await user.click(checkboxes[1]);
    expect(onToggle).toHaveBeenCalledWith("step-2", false);
  });

  it("renders empty state when no steps", () => {
    renderTracker([]);
    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
  });

  it("shows all-done message when all steps completed", () => {
    const allDone = SAMPLE_STEPS.map((s) => ({ ...s, completed: true }));
    renderTracker(allDone);
    expect(screen.getByText(/all steps completed/i)).toBeInTheDocument();
  });

  it("renders progress bar", () => {
    renderTracker();
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("renders in Spanish when locale is ES", () => {
    setLocale("es");
    renderTracker();
    expect(screen.getByText(/tu progreso/i)).toBeInTheDocument();
  });
});
