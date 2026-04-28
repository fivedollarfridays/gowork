import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";

vi.mock("@/components/layout/StallAlertBannerMount", () => ({
  StallAlertBannerMount: () => null,
}));

vi.mock("@/hooks/useLiveNowFormatted", () => ({
  useLiveNowFormatted: vi.fn(() => ({
    nowLabel: "12:34 PM",
    sessionCount: 7,
    lastCalibratedRelative: "5 minutes ago",
  })),
}));

import { Header } from "../Header";

describe("Header LiveNow widget (T4.A.5)", () => {
  beforeEach(() => setLocale("en"));

  it("does NOT render LiveNow on Ch1 (chapter <= 1)", () => {
    render(
      <TranslationProvider>
        <Header wallChapter={{ current: 1, total: 10 }} />
      </TranslationProvider>,
    );
    expect(screen.queryByTestId("live-now")).not.toBeInTheDocument();
  });

  it("does NOT render LiveNow when wallChapter is undefined (no wall)", () => {
    render(
      <TranslationProvider>
        <Header />
      </TranslationProvider>,
    );
    expect(screen.queryByTestId("live-now")).not.toBeInTheDocument();
  });

  it("renders LiveNow on chapters 2-10", () => {
    render(
      <TranslationProvider>
        <Header wallChapter={{ current: 4, total: 10 }} />
      </TranslationProvider>,
    );
    expect(screen.getByTestId("live-now")).toBeInTheDocument();
  });

  it("renders LiveNow on the final chapter", () => {
    render(
      <TranslationProvider>
        <Header wallChapter={{ current: 10, total: 10 }} />
      </TranslationProvider>,
    );
    expect(screen.getByTestId("live-now")).toBeInTheDocument();
  });
});
