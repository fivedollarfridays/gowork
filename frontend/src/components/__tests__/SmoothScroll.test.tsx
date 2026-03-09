import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockUseReducedMotion = vi.fn(() => false);
vi.mock("framer-motion", async () => {
  const actual = await vi.importActual("framer-motion");
  return { ...actual, useReducedMotion: () => mockUseReducedMotion() };
});

vi.mock("lenis/react", () => ({
  ReactLenis: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="lenis-wrapper">{children}</div>
  ),
}));

import { SmoothScroll } from "../SmoothScroll";

beforeEach(() => {
  mockUseReducedMotion.mockReturnValue(false);
});

describe("SmoothScroll", () => {
  it("renders children", () => {
    render(
      <SmoothScroll>
        <p>page content</p>
      </SmoothScroll>,
    );
    expect(screen.getByText("page content")).toBeInTheDocument();
  });

  it("with reduced motion renders children without lenis wrapper", () => {
    mockUseReducedMotion.mockReturnValue(true);
    render(
      <SmoothScroll>
        <p>accessible content</p>
      </SmoothScroll>,
    );
    expect(screen.getByText("accessible content")).toBeInTheDocument();
    expect(screen.queryByTestId("lenis-wrapper")).not.toBeInTheDocument();
  });

  it("without reduced motion renders with lenis wrapper", () => {
    render(
      <SmoothScroll>
        <p>smooth content</p>
      </SmoothScroll>,
    );
    expect(screen.getByText("smooth content")).toBeInTheDocument();
    expect(screen.getByTestId("lenis-wrapper")).toBeInTheDocument();
  });
});
