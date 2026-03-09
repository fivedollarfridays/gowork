import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

let mockPathname = "/";
vi.mock("next/navigation", () => ({
  usePathname: () => mockPathname,
}));

import { ViewTransitionsProvider } from "../ViewTransitionsProvider";

describe("ViewTransitionsProvider", () => {
  beforeEach(() => {
    mockPathname = "/";
  });

  it("renders children", () => {
    render(<ViewTransitionsProvider><p>content</p></ViewTransitionsProvider>);
    expect(screen.getByText("content")).toBeInTheDocument();
  });

  it("does not crash when startViewTransition is unavailable", () => {
    expect(() => {
      render(<ViewTransitionsProvider><p>safe</p></ViewTransitionsProvider>);
    }).not.toThrow();
    expect(screen.getByText("safe")).toBeInTheDocument();
  });

  it("calls startViewTransition when pathname changes and API is available", () => {
    const mockTransition = vi.fn();
    Object.defineProperty(document, "startViewTransition", {
      value: mockTransition,
      writable: true,
      configurable: true,
    });

    const { rerender } = render(
      <ViewTransitionsProvider><p>page1</p></ViewTransitionsProvider>,
    );

    mockPathname = "/new-page";
    rerender(<ViewTransitionsProvider><p>page2</p></ViewTransitionsProvider>);

    expect(mockTransition).toHaveBeenCalledTimes(1);

    // Cleanup
    delete (document as unknown as Record<string, unknown>).startViewTransition;
  });

  it("does not call startViewTransition when pathname is the same", () => {
    const mockTransition = vi.fn();
    Object.defineProperty(document, "startViewTransition", {
      value: mockTransition,
      writable: true,
      configurable: true,
    });

    const { rerender } = render(
      <ViewTransitionsProvider><p>same</p></ViewTransitionsProvider>,
    );

    rerender(<ViewTransitionsProvider><p>same</p></ViewTransitionsProvider>);

    expect(mockTransition).not.toHaveBeenCalled();

    delete (document as unknown as Record<string, unknown>).startViewTransition;
  });
});
