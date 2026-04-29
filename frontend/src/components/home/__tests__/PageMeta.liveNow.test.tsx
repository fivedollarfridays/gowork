/**
 * PageMeta — polish-2 T9.
 *
 * 5th row "LIVE — N sessions · last calibrated Mm ago" driven by
 * useLiveNow / useLiveNowFormatted.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";

vi.mock("@/hooks/useLiveNowFormatted", () => ({
  useLiveNowFormatted: vi.fn(),
}));

import { useLiveNowFormatted } from "@/hooks/useLiveNowFormatted";
import { PageMeta } from "../PageMeta";

function wrap(node: React.ReactNode) {
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

describe("PageMeta — LIVE row (T9)", () => {
  beforeEach(() => {
    setLocale("en");
    vi.mocked(useLiveNowFormatted).mockReturnValue({
      nowLabel: "9:14 AM",
      sessionCount: 18,
      lastCalibratedRelative: "14 minutes ago",
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders a LIVE label as a <dt>", () => {
    wrap(
      <PageMeta city="Fort Worth, TX" chapter={1} totalChapters={8} progress={0} hour={9} />,
    );
    const liveTerm = screen.getByText(/^LIVE$/);
    expect(liveTerm).toBeInTheDocument();
    expect(liveTerm.tagName.toLowerCase()).toBe("dt");
  });

  it("renders the sessions count and last-calibrated string in the LIVE <dd>", () => {
    const { container } = wrap(
      <PageMeta city="Fort Worth, TX" chapter={1} totalChapters={8} progress={0} hour={9} />,
    );
    const liveRow = container.querySelector("[data-page-meta-live]");
    expect(liveRow).toBeTruthy();
    expect(liveRow!.textContent).toMatch(/18/);
    expect(liveRow!.textContent).toMatch(/sessions/i);
    expect(liveRow!.textContent).toMatch(/14 minutes ago/);
  });

  it("renders Spanish copy when locale is es", () => {
    setLocale("es");
    const { container } = wrap(
      <PageMeta city="Fort Worth, TX" chapter={1} totalChapters={8} progress={0} hour={9} />,
    );
    const liveRow = container.querySelector("[data-page-meta-live]");
    expect(liveRow!.textContent).toMatch(/EN VIVO/);
    expect(liveRow!.textContent).toMatch(/sesiones/);
  });
});
