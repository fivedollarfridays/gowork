import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BenefitsEligibility } from "../BenefitsEligibility";
import type {
  BenefitsEligibility as BenefitsEligibilityType,
  ProgramEligibility,
} from "@/lib/types";

function makeProgram(overrides: Partial<ProgramEligibility> = {}): ProgramEligibility {
  return {
    program: "SNAP",
    eligible: true,
    confidence: "likely",
    income_threshold: 30000,
    income_headroom: 10000,
    estimated_monthly_value: 250,
    reason: "Income below 130% FPL",
    application_info: {
      application_url: "https://mydhr.alabama.gov",
      application_steps: ["Create account", "Complete application"],
      required_documents: ["Photo ID", "Proof of income"],
      office_name: "Montgomery County DHR",
      office_address: "1050 Government St, Montgomery, AL 36104",
      office_phone: "(334) 293-3100",
      processing_time: "30 days",
    },
    ...overrides,
  };
}

function makeEligibility(
  overrides: Partial<BenefitsEligibilityType> = {},
): BenefitsEligibilityType {
  return {
    eligible_programs: [
      makeProgram(),
      makeProgram({ program: "LIHEAP", estimated_monthly_value: 75, confidence: "possible" }),
    ],
    ineligible_programs: [
      makeProgram({ program: "Medicaid", eligible: false, estimated_monthly_value: 0, confidence: "unlikely", application_info: null }),
    ],
    total_estimated_monthly: 325,
    disclaimer: "This is an estimate. Contact DHR for official determination.",
    ...overrides,
  };
}

describe("BenefitsEligibility", () => {
  it("renders nothing when eligibility is null", () => {
    const { container } = render(<BenefitsEligibility eligibility={null} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders heading when eligibility provided", () => {
    render(<BenefitsEligibility eligibility={makeEligibility()} />);
    expect(screen.getByText(/benefits you may qualify for/i)).toBeDefined();
  });

  it("shows total estimated monthly value", () => {
    render(<BenefitsEligibility eligibility={makeEligibility()} />);
    expect(screen.getByText(/\$325/)).toBeDefined();
  });

  it("lists eligible programs", () => {
    render(<BenefitsEligibility eligibility={makeEligibility()} />);
    expect(screen.getByText("SNAP")).toBeDefined();
    expect(screen.getByText("LIHEAP")).toBeDefined();
  });

  it("shows estimated monthly value per program", () => {
    render(
      <BenefitsEligibility
        eligibility={makeEligibility({
          eligible_programs: [makeProgram({ estimated_monthly_value: 250 })],
        })}
      />,
    );
    expect(screen.getByText(/\$250\/mo/)).toBeDefined();
  });

  it("shows confidence badges with correct labels", () => {
    render(<BenefitsEligibility eligibility={makeEligibility()} />);
    expect(screen.getByText("Likely eligible")).toBeDefined();
    expect(screen.getByText("Possibly eligible")).toBeDefined();
  });

  it("shows income headroom per program", () => {
    render(
      <BenefitsEligibility
        eligibility={makeEligibility({
          eligible_programs: [makeProgram({ income_headroom: 10000 })],
        })}
      />,
    );
    expect(screen.getByText(/\$10,000 below threshold/i)).toBeDefined();
  });

  it("renders disclaimer text", () => {
    render(<BenefitsEligibility eligibility={makeEligibility()} />);
    expect(screen.getByText(/Contact DHR for official determination/i)).toBeDefined();
  });

  it("expands application details on click", async () => {
    const user = userEvent.setup();
    render(
      <BenefitsEligibility
        eligibility={makeEligibility({
          eligible_programs: [makeProgram()],
        })}
      />,
    );
    const trigger = screen.getByText(/how to apply/i);
    await user.click(trigger);
    expect(screen.getByText("Montgomery County DHR")).toBeDefined();
    expect(screen.getByText("(334) 293-3100")).toBeDefined();
  });

  it("distinguishes enrolled from additional eligible", () => {
    render(
      <BenefitsEligibility
        eligibility={makeEligibility()}
        enrolledPrograms={["SNAP"]}
      />,
    );
    expect(screen.getByText(/currently enrolled/i)).toBeDefined();
    expect(screen.getByText(/you may also qualify/i)).toBeDefined();
  });

  it("has accessible section landmark", () => {
    render(<BenefitsEligibility eligibility={makeEligibility()} />);
    const section = screen.getByRole("region", { name: /benefits eligibility/i });
    expect(section).toBeDefined();
  });
});
