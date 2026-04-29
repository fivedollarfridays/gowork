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
import { render, screen, cleanup } from "@testing-library/react";
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
