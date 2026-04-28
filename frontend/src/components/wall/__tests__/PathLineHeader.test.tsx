/**
 * W1 Driver C — T1.50 PathLineHeader.
 *
 * Persistent path-line at the top edge of the viewport that draws
 * further as scroll progresses. Tests guard the contract :
 *   - The line element is present and has aria-hidden (decorative).
 *   - The fill width responds to the `progress` prop (0–1 normalized).
 *   - When prefers-reduced-motion is set, the path renders fully
 *     filled (still an indicator, just static).
 */
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { PathLineHeader } from "../PathLineHeader";

describe("PathLineHeader (T1.50)", () => {
  it("renders an aria-hidden decorative line element", () => {
    const { container } = render(<PathLineHeader progress={0.4} />);
    const line = container.querySelector('[data-path-line]');
    expect(line).toBeInTheDocument();
    expect(line).toHaveAttribute("aria-hidden", "true");
  });

  it("translates progress 0..1 to width 0%..100% via inline style", () => {
    const { container } = render(<PathLineHeader progress={0.4} />);
    const fill = container.querySelector('[data-path-line-fill]') as HTMLElement;
    expect(fill).toBeInTheDocument();
    expect(fill.style.width).toBe("40%");
  });

  it("clamps progress >1 to 100%", () => {
    const { container } = render(<PathLineHeader progress={2.5} />);
    const fill = container.querySelector('[data-path-line-fill]') as HTMLElement;
    expect(fill.style.width).toBe("100%");
  });

  it("clamps progress <0 to 0%", () => {
    const { container } = render(<PathLineHeader progress={-0.3} />);
    const fill = container.querySelector('[data-path-line-fill]') as HTMLElement;
    expect(fill.style.width).toBe("0%");
  });

  it("renders 100% width when reducedMotion=true regardless of progress", () => {
    const { container } = render(
      <PathLineHeader progress={0.2} reducedMotion />,
    );
    const fill = container.querySelector('[data-path-line-fill]') as HTMLElement;
    expect(fill.style.width).toBe("100%");
  });
});
