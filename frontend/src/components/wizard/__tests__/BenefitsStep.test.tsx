import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BenefitsStep, BENEFITS_DEFAULTS } from "../BenefitsStep";
import type { BenefitsFormData } from "@/lib/types";

function renderStep(overrides: Partial<BenefitsFormData> = {}) {
  const data = { ...BENEFITS_DEFAULTS, ...overrides };
  const onChange = vi.fn();
  render(<BenefitsStep data={data} onChange={onChange} />);
  return { onChange, data };
}

describe("BenefitsStep", () => {
  it("renders household size input", () => {
    renderStep();
    expect(screen.getByLabelText(/household size/i)).toBeInTheDocument();
  });

  it("renders monthly income input", () => {
    renderStep();
    expect(screen.getByLabelText(/monthly income/i)).toBeInTheDocument();
  });

  it("renders all program checkboxes", () => {
    renderStep();
    expect(screen.getByLabelText(/SNAP/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/TANF/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Medicaid/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/ALL Kids/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Childcare Subsidy/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Section 8/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/LIHEAP/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/None of the above/i)).toBeInTheDocument();
  });

  it("renders dependents inputs", () => {
    renderStep();
    expect(screen.getByLabelText(/dependents under 6/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/dependents 6-17/i)).toBeInTheDocument();
  });

  it("calls onChange when program checked", async () => {
    const { onChange } = renderStep();
    const user = userEvent.setup();
    await user.click(screen.getByLabelText(/SNAP/i));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ enrolled_programs: ["SNAP"] })
    );
  });

  it("None checkbox clears enrolled programs", async () => {
    const { onChange } = renderStep({ enrolled_programs: ["SNAP", "TANF"] });
    const user = userEvent.setup();
    await user.click(screen.getByLabelText(/None of the above/i));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ enrolled_programs: [] })
    );
  });

  it("unchecking a program removes it", async () => {
    const { onChange } = renderStep({ enrolled_programs: ["SNAP", "TANF"] });
    const user = userEvent.setup();
    await user.click(screen.getByLabelText(/SNAP/i));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ enrolled_programs: ["TANF"] })
    );
  });

  it("displays with defaults when no overrides", () => {
    renderStep();
    const householdInput = screen.getByLabelText(/household size/i) as HTMLInputElement;
    expect(householdInput.value).toBe("1");
  });
});
