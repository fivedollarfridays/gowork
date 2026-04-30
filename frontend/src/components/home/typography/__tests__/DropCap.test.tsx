/**
 * Driver C — polish-2 T36 — DropCap component contract.
 *
 * The component renders an inline span with the `dropcap` class, a
 * per-chapter `data-chapter` attribute, and a stable test id. The
 * `::first-letter` styling and per-chapter color tokens live in
 * `home-chapters.css`.
 */
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { DropCap } from "../DropCap";

describe("DropCap — T36", () => {
  it("renders chapter=3 with data-chapter='3'", () => {
    const { container } = render(<DropCap chapter="3">A name on every street.</DropCap>);
    const span = container.querySelector(".dropcap");
    expect(span).not.toBeNull();
    expect(span?.getAttribute("data-chapter")).toBe("3");
    expect(span?.textContent).toMatch(/A name on every street/);
  });

  it("renders chapter=7 with data-chapter='7'", () => {
    const { container } = render(<DropCap chapter="7">At $18.50 the cliff bites.</DropCap>);
    const span = container.querySelector(".dropcap");
    expect(span?.getAttribute("data-chapter")).toBe("7");
  });

  it("renders chapter=8 with data-chapter='8'", () => {
    const { container } = render(<DropCap chapter="8">We will not fix the wall.</DropCap>);
    const span = container.querySelector(".dropcap");
    expect(span?.getAttribute("data-chapter")).toBe("8");
  });

  it("merges custom className", () => {
    const { container } = render(
      <DropCap chapter="3" className="extra-cls">x</DropCap>,
    );
    const span = container.querySelector(".dropcap");
    expect(span?.className).toContain("dropcap");
    expect(span?.className).toContain("extra-cls");
  });

  it("emits a data-testid for visual snapshots", () => {
    const { getByTestId } = render(<DropCap chapter="7">x</DropCap>);
    expect(getByTestId("dropcap-ch7")).toBeInTheDocument();
  });
});
