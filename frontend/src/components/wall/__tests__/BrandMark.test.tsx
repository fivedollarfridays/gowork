/**
 * BrandMark component tests — T1.107 wrapper + loading + interactive.
 */
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { BrandMark } from "../BrandMark";

function svgFor(node: HTMLElement | SVGElement | null): SVGElement {
  if (!node) throw new Error("expected node");
  return node as SVGElement;
}

describe("BrandMark — geometry + accessibility", () => {
  it("renders an svg with role=img and aria-label", () => {
    const { container } = render(<BrandMark />);
    const svg = svgFor(container.querySelector("svg"));
    expect(svg).toHaveAttribute("role", "img");
    expect(svg).toHaveAttribute("aria-label", "GoWork");
  });

  it("uses the canonical 16-coordinate viewBox", () => {
    const { container } = render(<BrandMark />);
    const svg = svgFor(container.querySelector("svg"));
    expect(svg).toHaveAttribute("viewBox", "0 0 16 16");
  });

  it("renders the cyan path-line inside a path-draw wrapper for T1.107", () => {
    const { container } = render(<BrandMark />);
    const wrapper = container.querySelector(".path-draw");
    expect(wrapper).toBeTruthy();
    const line = wrapper?.querySelector("line.gowork-mark__path");
    expect(line).toBeTruthy();
    expect(line?.getAttribute("stroke")).toBe("#22D3EE");
  });

  it("can hide the path-line via showPath=false (used in compact contexts)", () => {
    const { container } = render(<BrandMark showPath={false} />);
    expect(container.querySelector(".gowork-mark__path")).toBeNull();
  });
});

describe("BrandMark — T1.107 interactive + loading", () => {
  it("does NOT add gowork-mark--hover class by default", () => {
    const { container } = render(<BrandMark />);
    const svg = svgFor(container.querySelector("svg"));
    expect(svg.className.baseVal).not.toMatch(/gowork-mark--hover/);
  });

  it("adds gowork-mark--hover class when interactive=true", () => {
    const { container } = render(<BrandMark interactive />);
    const svg = svgFor(container.querySelector("svg"));
    expect(svg.className.baseVal).toMatch(/gowork-mark--hover/);
  });

  it("adds brand-loading class when loading=true", () => {
    const { container } = render(<BrandMark loading />);
    const svg = svgFor(container.querySelector("svg"));
    expect(svg.className.baseVal).toMatch(/brand-loading/);
  });

  it("preserves user-supplied className", () => {
    const { container } = render(<BrandMark className="custom" interactive />);
    const svg = svgFor(container.querySelector("svg"));
    expect(svg.className.baseVal).toMatch(/custom/);
    expect(svg.className.baseVal).toMatch(/gowork-mark/);
  });
});
