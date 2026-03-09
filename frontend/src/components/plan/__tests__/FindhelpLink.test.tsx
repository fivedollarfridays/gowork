import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { FindhelpLink } from "../FindhelpLink";
import { BarrierType } from "@/lib/types";
import { FINDHELP_CATEGORIES, generateFindhelpUrl } from "@/lib/findhelp";

describe("generateFindhelpUrl", () => {
  it("generates URL for credit barrier", () => {
    const url = generateFindhelpUrl(BarrierType.CREDIT, "36104");
    expect(url).toContain("findhelp.org");
    expect(url).toContain("financial-assistance");
    expect(url).toContain("postal=36104");
  });

  it("generates URL for all 7 barrier types", () => {
    for (const bt of Object.values(BarrierType)) {
      const url = generateFindhelpUrl(bt, "36104");
      expect(url).not.toBeNull();
      expect(url).toContain("findhelp.org");
    }
  });

  it("returns null for unknown barrier", () => {
    const url = generateFindhelpUrl("unknown" as BarrierType, "36104");
    expect(url).toBeNull();
  });

  it("embeds different zip codes", () => {
    const url1 = generateFindhelpUrl(BarrierType.HOUSING, "36101");
    const url2 = generateFindhelpUrl(BarrierType.HOUSING, "36117");
    expect(url1).toContain("36101");
    expect(url2).toContain("36117");
  });
});

describe("FINDHELP_CATEGORIES", () => {
  it("has mapping for all barrier types", () => {
    for (const bt of Object.values(BarrierType)) {
      expect(FINDHELP_CATEGORIES[bt]).toBeDefined();
    }
  });
});

describe("FindhelpLink", () => {
  it("renders a link with correct href", () => {
    render(<FindhelpLink barrierType={BarrierType.CREDIT} zipCode="36104" />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", expect.stringContaining("findhelp.org"));
    expect(link).toHaveAttribute("href", expect.stringContaining("financial-assistance"));
    expect(link).toHaveAttribute("href", expect.stringContaining("postal=36104"));
  });

  it("opens in new tab", () => {
    render(<FindhelpLink barrierType={BarrierType.HOUSING} zipCode="36104" />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", expect.stringContaining("noopener"));
  });

  it("displays descriptive text", () => {
    render(<FindhelpLink barrierType={BarrierType.CHILDCARE} zipCode="36104" />);
    expect(screen.getByText(/more programs/i)).toBeInTheDocument();
  });

  it("renders nothing for unknown barrier type", () => {
    const { container } = render(
      <FindhelpLink barrierType={"unknown" as BarrierType} zipCode="36104" />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing when zipCode is empty", () => {
    const { container } = render(
      <FindhelpLink barrierType={BarrierType.CREDIT} zipCode="" />
    );
    expect(container.firstChild).toBeNull();
  });
});
