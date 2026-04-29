/**
 * Home CursorFlashlight — soft 480x480 amber glow that follows the
 * cursor across the WHOLE page (not just the map). Distinct from the
 * existing wall/MapCursorFlashlight which lives inside the Mapbox canvas.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { CursorFlashlight } from "../CursorFlashlight";

describe("CursorFlashlight (home)", () => {
  it("renders without crashing as an aria-hidden overlay", () => {
    const { container } = render(<CursorFlashlight />);
    const overlay = container.querySelector("[data-home-cursor-flashlight]");
    expect(overlay).toBeTruthy();
    expect(overlay).toHaveAttribute("aria-hidden", "true");
  });

  it("uses fixed positioning so it tracks the viewport, not a parent", () => {
    const { container } = render(<CursorFlashlight />);
    const overlay = container.querySelector("[data-home-cursor-flashlight]") as HTMLElement | null;
    expect(overlay).toBeTruthy();
    expect(overlay?.style.position).toBe("fixed");
  });

  it("uses pointer-events: none so it never intercepts clicks", () => {
    const { container } = render(<CursorFlashlight />);
    const overlay = container.querySelector("[data-home-cursor-flashlight]") as HTMLElement | null;
    expect(overlay?.style.pointerEvents).toBe("none");
  });

  it("uses mix-blend-mode: screen for additive light", () => {
    const { container } = render(<CursorFlashlight />);
    const overlay = container.querySelector("[data-home-cursor-flashlight]") as HTMLElement | null;
    expect(overlay?.style.mixBlendMode).toBe("screen");
  });

  it("does not render when prefers coarse pointer is signalled via prop", () => {
    const { container } = render(<CursorFlashlight forceDisabled />);
    expect(container.querySelector("[data-home-cursor-flashlight]")).toBeNull();
  });
});
