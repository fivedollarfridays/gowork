import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { JobFilters } from "@/components/plan/JobFilters";
import { JobFilterPills } from "@/components/plan/JobFilterPills";
import { defaultFilters, type JobFilterState } from "@/lib/jobFilters";

describe("JobFilters", () => {
  it("renders source select", () => {
    render(<JobFilters filters={defaultFilters} onChange={vi.fn()} />);
    expect(screen.getByLabelText(/source/i)).toBeInTheDocument();
  });

  it("renders fair-chance checkbox", () => {
    render(<JobFilters filters={defaultFilters} onChange={vi.fn()} />);
    expect(
      screen.getByRole("checkbox", { name: /fair.chance/i }),
    ).toBeInTheDocument();
  });

  it("renders schedule select", () => {
    render(<JobFilters filters={defaultFilters} onChange={vi.fn()} />);
    expect(screen.getByLabelText(/schedule/i)).toBeInTheDocument();
  });

  it("calls onChange when fair-chance checkbox toggled", () => {
    const onChange = vi.fn();
    render(<JobFilters filters={defaultFilters} onChange={onChange} />);
    fireEvent.click(screen.getByRole("checkbox", { name: /fair.chance/i }));
    expect(onChange).toHaveBeenCalledWith({
      ...defaultFilters,
      fairChanceOnly: true,
    });
  });

  it("shows filter count in header when filters active", () => {
    const filters: JobFilterState = {
      ...defaultFilters,
      source: "honestjobs",
      fairChanceOnly: true,
    };
    render(<JobFilters filters={filters} onChange={vi.fn()} />);
    expect(screen.getByText(/2 active/i)).toBeInTheDocument();
  });

  it("does not show count when no filters active", () => {
    render(<JobFilters filters={defaultFilters} onChange={vi.fn()} />);
    expect(screen.queryByText(/active/i)).not.toBeInTheDocument();
  });
});

describe("JobFilterPills", () => {
  it("renders nothing when default filters", () => {
    const { container } = render(
      <JobFilterPills filters={defaultFilters} onClear={vi.fn()} />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders pill for source filter", () => {
    const filters: JobFilterState = { ...defaultFilters, source: "honestjobs" };
    render(<JobFilterPills filters={filters} onClear={vi.fn()} />);
    expect(screen.getByText(/honest jobs/i)).toBeInTheDocument();
  });

  it("renders pill for fair-chance filter", () => {
    const filters: JobFilterState = {
      ...defaultFilters,
      fairChanceOnly: true,
    };
    render(<JobFilterPills filters={filters} onClear={vi.fn()} />);
    expect(screen.getByText(/fair.chance/i)).toBeInTheDocument();
  });

  it("renders pill for schedule filter", () => {
    const filters: JobFilterState = { ...defaultFilters, schedule: "full-time" };
    render(<JobFilterPills filters={filters} onClear={vi.fn()} />);
    expect(screen.getByText(/full.time/i)).toBeInTheDocument();
  });

  it("shows clear all button when filters active", () => {
    const filters: JobFilterState = {
      ...defaultFilters,
      fairChanceOnly: true,
    };
    render(<JobFilterPills filters={filters} onClear={vi.fn()} />);
    expect(
      screen.getByRole("button", { name: /clear all/i }),
    ).toBeInTheDocument();
  });

  it("calls onClear with default filters on clear all click", () => {
    const onClear = vi.fn();
    const filters: JobFilterState = {
      ...defaultFilters,
      fairChanceOnly: true,
    };
    render(<JobFilterPills filters={filters} onClear={onClear} />);
    fireEvent.click(screen.getByRole("button", { name: /clear all/i }));
    expect(onClear).toHaveBeenCalledWith(defaultFilters);
  });

  it("dismisses individual pill", () => {
    const onClear = vi.fn();
    const filters: JobFilterState = {
      ...defaultFilters,
      source: "jsearch",
      fairChanceOnly: true,
    };
    render(<JobFilterPills filters={filters} onClear={onClear} />);
    // Click the dismiss button on the fair-chance pill
    const pill = screen.getByRole("button", { name: /remove fair.chance/i });
    fireEvent.click(pill);
    expect(onClear).toHaveBeenCalledWith({
      ...filters,
      fairChanceOnly: false,
    });
  });
});
