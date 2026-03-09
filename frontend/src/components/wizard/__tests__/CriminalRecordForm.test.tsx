import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CriminalRecordForm } from "../CriminalRecordForm";
import type { RecordProfile } from "@/lib/types";

const emptyProfile: RecordProfile = {
  record_types: [],
  charge_categories: [],
  years_since_conviction: null,
  completed_sentence: false,
};

describe("CriminalRecordForm", () => {
  it("renders privacy notice", () => {
    render(<CriminalRecordForm data={emptyProfile} onChange={vi.fn()} />);
    expect(screen.getByText(/your privacy is protected/i)).toBeInTheDocument();
    expect(screen.getByText(/never shared with employers/i)).toBeInTheDocument();
  });

  it("renders all record type options", () => {
    render(<CriminalRecordForm data={emptyProfile} onChange={vi.fn()} />);
    expect(screen.getByText("Felony")).toBeInTheDocument();
    expect(screen.getByText("Misdemeanor")).toBeInTheDocument();
    expect(screen.getByText(/arrest only/i)).toBeInTheDocument();
    expect(screen.getByText(/expunged/i)).toBeInTheDocument();
  });

  it("renders all charge category options", () => {
    render(<CriminalRecordForm data={emptyProfile} onChange={vi.fn()} />);
    expect(screen.getByText(/theft/i)).toBeInTheDocument();
    expect(screen.getByText(/drug/i)).toBeInTheDocument();
    expect(screen.getByText(/dui/i)).toBeInTheDocument();
    expect(screen.getByText(/fraud/i)).toBeInTheDocument();
    expect(screen.getByText(/violence/i)).toBeInTheDocument();
    expect(screen.getByText(/sex offense/i)).toBeInTheDocument();
  });

  it("calls onChange when record type toggled", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<CriminalRecordForm data={emptyProfile} onChange={onChange} />);

    await user.click(screen.getByText("Felony"));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ record_types: ["felony"] }),
    );
  });

  it("calls onChange when years input changes", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<CriminalRecordForm data={emptyProfile} onChange={onChange} />);

    const yearsInput = screen.getByLabelText(/years since conviction/i);
    await user.type(yearsInput, "5");
    expect(onChange).toHaveBeenCalled();
  });

  it("calls onChange when sentence checkbox toggled", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<CriminalRecordForm data={emptyProfile} onChange={onChange} />);

    await user.click(screen.getByText(/completed my sentence/i));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ completed_sentence: true }),
    );
  });
});
