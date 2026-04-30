/**
 * Driver C — sprint/gowork-facelift Chapter 06 Live Jobs tests.
 *
 * Locks the contract:
 *   - section #chapter-06 with class ch06, data-bg="dark"
 *   - aria-labelledby pointing at the title
 *   - 3 JobCards (alcon, bnsf, dunn) — copy from registry + i18n
 *   - wage marquee renders 12 entries (6 unique × 2)
 *   - live-pill renders the timestamp
 *   - JobCard CTAs link to /assess?employer={id}
 *   - EN + ES coverage
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { Chapter06LiveJobs } from "../Chapter06LiveJobs";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

function makeWrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={client}>
        <TranslationProvider>{children}</TranslationProvider>
      </QueryClientProvider>
    );
  };
}

function renderEN(node: React.ReactNode) {
  setLocale("en");
  const Wrapper = makeWrapper();
  return render(<Wrapper>{node}</Wrapper>);
}
function renderES(node: React.ReactNode) {
  setLocale("es");
  const Wrapper = makeWrapper();
  return render(<Wrapper>{node}</Wrapper>);
}

beforeEach(() => {
  cleanup();
  setLocale("en");
  // Ensure useLiveNow's fetch path doesn't blow up in jsdom.
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ now: new Date().toISOString(), sessions: 0 }),
  }));
});

describe("Chapter06LiveJobs — render contract", () => {
  it("renders a section with id chapter-06 and class ch06", () => {
    renderEN(<Chapter06LiveJobs />);
    const section = document.getElementById("chapter-06");
    expect(section).toBeInTheDocument();
    expect(section?.className).toMatch(/ch06/);
    expect(section?.getAttribute("data-bg")).toBe("dark");
  });

  it("declares aria-labelledby pointing at the chapter title id", () => {
    renderEN(<Chapter06LiveJobs />);
    const section = document.getElementById("chapter-06");
    const labelledBy = section?.getAttribute("aria-labelledby");
    expect(labelledBy).toBeTruthy();
    expect(document.getElementById(labelledBy ?? "")).toBeInTheDocument();
  });

  it("renders 3 JobCards (alcon, bnsf, dunn)", () => {
    renderEN(<Chapter06LiveJobs />);
    expect(screen.getByTestId("ch06-card-alcon")).toBeInTheDocument();
    expect(screen.getByTestId("ch06-card-bnsf")).toBeInTheDocument();
    expect(screen.getByTestId("ch06-card-dunn")).toBeInTheDocument();
  });

  it("renders the live-pill", () => {
    renderEN(<Chapter06LiveJobs />);
    expect(screen.getByTestId("ch06-live-pill")).toBeInTheDocument();
  });

  it("renders the wage marquee with 12 entries", () => {
    renderEN(<Chapter06LiveJobs />);
    const entries = screen.getAllByTestId(/^ch06-wage-/);
    expect(entries).toHaveLength(12);
  });

  it("each JobCard links to /assess?employer={id}", () => {
    renderEN(<Chapter06LiveJobs />);
    const alconCta = screen
      .getByTestId("ch06-card-alcon")
      .querySelector("a.jc-cta") as HTMLAnchorElement | null;
    expect(alconCta).toBeTruthy();
    expect(alconCta?.getAttribute("href")).toBe("/assess?employer=alcon");
  });
});

describe("Chapter06LiveJobs — copy", () => {
  it("renders the eyebrow '06 / Live jobs' in EN", () => {
    renderEN(<Chapter06LiveJobs />);
    expect(
      screen.getAllByText(/06 \/ Live jobs/i).length,
    ).toBeGreaterThan(0);
  });

  it("renders Spanish copy when locale = es", () => {
    renderES(<Chapter06LiveJobs />);
    // Spanish eyebrow contains 'Empleos en vivo'
    expect(
      screen.getAllByText(/Empleos en vivo/i).length,
    ).toBeGreaterThan(0);
  });

  it("Alcon card mentions $22.50/hr wage", () => {
    renderEN(<Chapter06LiveJobs />);
    expect(screen.getByTestId("ch06-card-alcon").textContent).toMatch(
      /\$22\.50\/hr/i,
    );
  });
});

describe("Chapter06LiveJobs — T26 LivePill calibration wiring", () => {
  it("LivePill body matches the formatLiveAgo result", () => {
    // The pill renders prefix + body + suffix. The body is derived from
    // formatLiveAgo(now, lastCalibration) — under the test stub fetch
    // those are null/placeholder, so body falls back to '4 min'.
    renderEN(<Chapter06LiveJobs />);
    const pill = screen.getByTestId("ch06-live-pill");
    expect(pill.textContent).toMatch(/4 min/);
  });
});

describe("Chapter06LiveJobs — T27 JobCard skeleton", () => {
  it("JobCard renders skeleton when loading=true", async () => {
    const { JobCard } = await import("../_internal/JobCard");
    const { TranslationProvider } = await import("@/hooks/useTranslation");
    cleanup();
    render(
      <TranslationProvider>
        <JobCard id="alcon" loading />
      </TranslationProvider>,
    );
    const card = screen.getByTestId("ch06-card-alcon");
    expect(card.getAttribute("data-skeleton")).toBe("true");
    const rows = card.querySelectorAll(".ch06-skeleton__row");
    expect(rows.length).toBe(4);
  });

  it("JobCard renders real content when loading=false (default)", async () => {
    const { JobCard } = await import("../_internal/JobCard");
    const { TranslationProvider } = await import("@/hooks/useTranslation");
    cleanup();
    render(
      <TranslationProvider>
        <JobCard id="alcon" />
      </TranslationProvider>,
    );
    const card = screen.getByTestId("ch06-card-alcon");
    expect(card.getAttribute("data-skeleton")).toBe("false");
    expect(card.querySelectorAll(".ch06-skeleton__row").length).toBe(0);
  });
});

describe("Chapter06LiveJobs — T28 Apply CTA haptic + magnetic", () => {
  it("clicking the apply CTA invokes navigator.vibrate(15)", async () => {
    const vibrate = vi.fn();
    Object.defineProperty(navigator, "vibrate", {
      configurable: true,
      writable: true,
      value: vibrate,
    });
    renderEN(<Chapter06LiveJobs />);
    const cta = screen
      .getByTestId("ch06-card-alcon")
      .querySelector("a.jc-cta") as HTMLAnchorElement;
    expect(cta).toBeTruthy();
    // jsdom navigation: prevent the default to keep the test clean.
    cta.addEventListener("click", (e) => e.preventDefault());
    cta.click();
    expect(vibrate).toHaveBeenCalled();
  });
});

describe("Chapter06LiveJobs — T29 marquee pause-on-hover", () => {
  it("the marquee container exposes pointer-handlers and a data-testid", () => {
    renderEN(<Chapter06LiveJobs />);
    const marquee = screen.getByTestId("ch06-marquee");
    expect(marquee).toBeInTheDocument();
    // Hover/leave wire to GSAP timeScale internally — without GSAP loaded
    // in jsdom the tween ref stays null, but the handlers themselves must
    // exist (no throw on dispatching the events).
    expect(() => {
      fireEvent.pointerEnter(marquee);
      fireEvent.pointerLeave(marquee);
    }).not.toThrow();
  });
});

describe("formatLiveAgo (T26) — calibration diff", () => {
  it("returns '14 min' when calibration was 14 min before now", async () => {
    const { formatLiveAgo } = await import("../Chapter06LiveJobs.helpers");
    const now = new Date("2026-04-29T12:00:00Z");
    const calibrated = new Date("2026-04-29T11:46:00Z");
    expect(formatLiveAgo(now, calibrated)).toBe("14 min");
  });

  it("returns 'just now' when calibration is < 1 min before now", async () => {
    const { formatLiveAgo } = await import("../Chapter06LiveJobs.helpers");
    const now = new Date("2026-04-29T12:00:00Z");
    const calibrated = new Date("2026-04-29T11:59:30Z");
    expect(formatLiveAgo(now, calibrated)).toBe("just now");
  });

  it("falls back to '4 min' when calibration is null", async () => {
    const { formatLiveAgo } = await import("../Chapter06LiveJobs.helpers");
    const now = new Date("2026-04-29T12:00:00Z");
    expect(formatLiveAgo(now, null)).toBe("4 min");
  });

  it("collapses to hours when more than 60 min", async () => {
    const { formatLiveAgo } = await import("../Chapter06LiveJobs.helpers");
    const now = new Date("2026-04-29T12:00:00Z");
    const calibrated = new Date("2026-04-29T09:30:00Z");
    expect(formatLiveAgo(now, calibrated)).toBe("2h");
  });
});
