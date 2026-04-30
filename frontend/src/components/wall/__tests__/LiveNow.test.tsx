import { describe, it, expect, vi, afterEach } from "vitest";
import { render } from "@testing-library/react";
import { LiveNow } from "../LiveNow";

vi.mock("../../../hooks/useLiveNowFormatted", () => ({
  useLiveNowFormatted: vi.fn(),
}));

import { useLiveNowFormatted } from "../../../hooks/useLiveNowFormatted";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("LiveNow component (T4.A.5)", () => {
  it("renders the formatted now label", () => {
    vi.mocked(useLiveNowFormatted).mockReturnValue({
      nowLabel: "7:42 PM",
      sessionCount: 12,
      lastCalibratedRelative: "14 minutes ago",
    });
    const { getByTestId } = render(<LiveNow />);
    const root = getByTestId("live-now");
    expect(root.textContent).toContain("7:42 PM");
  });

  it("renders the session count with monospace tabular-nums utility", () => {
    vi.mocked(useLiveNowFormatted).mockReturnValue({
      nowLabel: "noon",
      sessionCount: 12,
      lastCalibratedRelative: "now",
    });
    const { getByTestId } = render(<LiveNow />);
    const sessions = getByTestId("live-now-sessions");
    expect(sessions.textContent).toContain("12");
    // Tabular nums via inline style or Tailwind class. Our component
    // sets fontVariantNumeric inline.
    expect(sessions.style.fontVariantNumeric).toContain("tabular");
  });

  it("renders the last-calibration relative string", () => {
    vi.mocked(useLiveNowFormatted).mockReturnValue({
      nowLabel: "noon",
      sessionCount: 12,
      lastCalibratedRelative: "14 minutes ago",
    });
    const { getByTestId } = render(<LiveNow />);
    const cal = getByTestId("live-now-calibration");
    expect(cal.textContent).toContain("14 minutes ago");
  });

  it("returns null when hidden=true (Ch1 hero)", () => {
    vi.mocked(useLiveNowFormatted).mockReturnValue({
      nowLabel: "noon",
      sessionCount: 12,
      lastCalibratedRelative: "now",
    });
    const { container } = render(<LiveNow hidden />);
    expect(container.firstChild).toBeNull();
  });

  it("renders an aria-live=polite region for screen reader updates", () => {
    vi.mocked(useLiveNowFormatted).mockReturnValue({
      nowLabel: "1:00 PM",
      sessionCount: 5,
      lastCalibratedRelative: "now",
    });
    const { getByTestId } = render(<LiveNow />);
    const root = getByTestId("live-now");
    expect(root.getAttribute("aria-live")).toBe("polite");
  });

  it("respects locale prop forwarded to the hook", () => {
    vi.mocked(useLiveNowFormatted).mockReturnValue({
      nowLabel: "13:00",
      sessionCount: 5,
      lastCalibratedRelative: "ahora",
    });
    render(<LiveNow locale="es-MX" />);
    expect(vi.mocked(useLiveNowFormatted)).toHaveBeenCalledWith("es-MX");
  });
});
