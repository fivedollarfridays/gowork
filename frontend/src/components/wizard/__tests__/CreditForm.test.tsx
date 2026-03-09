import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { CreditForm } from "../CreditForm";
import type { CreditFormData } from "@/lib/types";

function defaultData(): CreditFormData {
  return {
    currentScore: 650,
    overallUtilization: 30,
    paymentHistoryPct: 90,
    accountAgeRange: "1-3y",
    totalAccounts: 3,
    openAccounts: 2,
    collectionAccounts: 0,
    negativeItems: [],
  };
}

describe("CreditForm — a11y label associations (WCAG 1.3.1)", () => {
  it("Credit Score label is associated with slider via aria-labelledby", () => {
    render(<CreditForm data={defaultData()} onChange={vi.fn()} />);
    const slider = screen.getByRole("slider", { name: /credit score/i });
    expect(slider).toBeInTheDocument();
  });

  it("Credit Utilization label is associated with slider via aria-labelledby", () => {
    render(<CreditForm data={defaultData()} onChange={vi.fn()} />);
    const slider = screen.getByRole("slider", { name: /credit utilization/i });
    expect(slider).toBeInTheDocument();
  });

  it("Payment History label is associated with slider via aria-labelledby", () => {
    render(<CreditForm data={defaultData()} onChange={vi.fn()} />);
    const slider = screen.getByRole("slider", { name: /payment history/i });
    expect(slider).toBeInTheDocument();
  });

  it("Total accounts input is accessible by label", () => {
    render(<CreditForm data={defaultData()} onChange={vi.fn()} />);
    expect(screen.getByLabelText(/total accounts/i)).toBeInTheDocument();
  });

  it("Still open input is accessible by label", () => {
    render(<CreditForm data={defaultData()} onChange={vi.fn()} />);
    expect(screen.getByLabelText(/still open/i)).toBeInTheDocument();
  });

  it("In collections input is accessible by label", () => {
    render(<CreditForm data={defaultData()} onChange={vi.fn()} />);
    expect(screen.getByLabelText(/in collections/i)).toBeInTheDocument();
  });
});
