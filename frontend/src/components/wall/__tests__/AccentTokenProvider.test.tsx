import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render } from "@testing-library/react";
import { AccentTokenProvider } from "../AccentTokenProvider";

vi.mock("../../../hooks/useTimeOfDay", () => ({
  useTimeOfDay: vi.fn(),
}));

import { useTimeOfDay } from "../../../hooks/useTimeOfDay";

describe("AccentTokenProvider (T4.A.2)", () => {
  beforeEach(() => {
    document.documentElement.style.removeProperty("--accent-current");
  });

  afterEach(() => {
    document.documentElement.style.removeProperty("--accent-current");
    vi.restoreAllMocks();
  });

  it("sets --accent-current on the document root from useTimeOfDay", () => {
    vi.mocked(useTimeOfDay).mockReturnValue({
      phase: "day",
      sunPosition: 0.85,
      accentShift: "cyan",
      sunAltitudeDeg: 76,
      skyTypeName: "atmosphere",
      skyColor: "oklch(0.88 0.08 240)",
      accentToken: "blue",
    });
    render(<AccentTokenProvider />);
    const value = document.documentElement.style.getPropertyValue("--accent-current");
    expect(value).toBeTruthy();
    expect(value).toMatch(/blue|oklch/);
  });

  it("updates --accent-current when phase changes (rerender)", () => {
    vi.mocked(useTimeOfDay).mockReturnValue({
      phase: "morning",
      sunPosition: 0.4,
      accentShift: "rose",
      sunAltitudeDeg: 36,
      skyTypeName: "atmosphere",
      skyColor: "oklch(0.85 0.07 220)",
      accentToken: "cyan",
    });
    const { rerender } = render(<AccentTokenProvider />);
    const first = document.documentElement.style.getPropertyValue("--accent-current");
    expect(first).toBeTruthy();

    vi.mocked(useTimeOfDay).mockReturnValue({
      phase: "evening",
      sunPosition: 0.2,
      accentShift: "amber",
      sunAltitudeDeg: 18,
      skyTypeName: "gradient",
      skyColor: "oklch(0.55 0.12 30)",
      accentToken: "rose",
    });
    rerender(<AccentTokenProvider />);
    const second = document.documentElement.style.getPropertyValue("--accent-current");
    expect(second).toBeTruthy();
    expect(second).not.toBe(first);
  });

  it("renders nothing visible (zero DOM footprint)", () => {
    vi.mocked(useTimeOfDay).mockReturnValue({
      phase: "day",
      sunPosition: 0.5,
      accentShift: "cyan",
      sunAltitudeDeg: 45,
      skyTypeName: "atmosphere",
      skyColor: "oklch(0.85 0.05 230)",
      accentToken: "blue",
    });
    const { container } = render(<AccentTokenProvider />);
    expect(container.firstChild).toBeNull();
  });
});
