/**
 * HomePage — polish-2 Driver E mount-order tests.
 *
 * Verifies the spotlight bridges and gates are mounted alongside the
 * existing chrome:
 *   - TitleSequenceGate (T49)
 *   - Ch01CursorTrail   (T48)
 *   - ScrollVelocityBridge (T56/57/59)
 *   - EyebrowActiveBridge  (T55)
 *   - FpsOverlayGate    (T54)
 */
import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, cleanup } from "@testing-library/react";
import { TranslationProvider } from "@/hooks/useTranslation";

vi.mock("@/components/home/SiteHeader", () => ({
  SiteHeader: () =>
    React.createElement("div", { "data-testid": "stub-site-header" }),
}));
vi.mock("@/components/home/SiteFooter", () => ({
  SiteFooter: () =>
    React.createElement("div", { "data-testid": "stub-site-footer" }),
}));
vi.mock("@/components/home/ChapterRail", () => ({
  ChapterRail: () =>
    React.createElement("div", { "data-testid": "stub-chapter-rail" }),
}));
vi.mock("@/components/home/PageMeta", () => ({
  PageMeta: () =>
    React.createElement("div", { "data-testid": "stub-page-meta" }),
}));
vi.mock("@/components/home/CursorFlashlight", () => ({
  CursorFlashlight: () =>
    React.createElement("div", { "data-testid": "stub-cursor-flashlight" }),
}));

vi.mock("@/components/home/TitleSequenceGate", () => ({
  TitleSequenceGate: () =>
    React.createElement("div", { "data-testid": "stub-title-gate" }),
}));
vi.mock("@/components/home/Ch01CursorTrail", () => ({
  Ch01CursorTrail: () =>
    React.createElement("div", { "data-testid": "stub-ch01-trail" }),
}));
vi.mock("@/components/home/ScrollVelocityBridge", () => ({
  ScrollVelocityBridge: () =>
    React.createElement("div", { "data-testid": "stub-velocity-bridge" }),
}));
vi.mock("@/components/home/EyebrowActiveBridge", () => ({
  EyebrowActiveBridge: () =>
    React.createElement("div", { "data-testid": "stub-eyebrow-bridge" }),
}));
vi.mock("@/components/home/FpsOverlayGate", () => ({
  FpsOverlayGate: () =>
    React.createElement("div", { "data-testid": "stub-fps-gate" }),
}));

const installSoundTriggersMock = vi.fn(() => () => undefined);
vi.mock("@/lib/home/soundTriggers", () => ({
  installSoundTriggers: () => installSoundTriggersMock(),
}));

vi.mock("next/dynamic", () => ({
  default: () =>
    function ChapterStub() {
      return React.createElement("section", null, null);
    },
}));

afterEach(() => {
  cleanup();
  installSoundTriggersMock.mockClear();
});

function wrap(node: React.ReactElement) {
  return render(<TranslationProvider>{node}</TranslationProvider>);
}

describe("HomePage — polish-2 spotlight wiring", () => {
  it("mounts the TitleSequenceGate", async () => {
    const { default: HomePage } = await import("../HomePage");
    const { getByTestId } = wrap(<HomePage />);
    expect(getByTestId("stub-title-gate")).toBeInTheDocument();
  });

  it("mounts the Ch01CursorTrail", async () => {
    const { default: HomePage } = await import("../HomePage");
    const { getByTestId } = wrap(<HomePage />);
    expect(getByTestId("stub-ch01-trail")).toBeInTheDocument();
  });

  it("mounts the ScrollVelocityBridge", async () => {
    const { default: HomePage } = await import("../HomePage");
    const { getByTestId } = wrap(<HomePage />);
    expect(getByTestId("stub-velocity-bridge")).toBeInTheDocument();
  });

  it("mounts the EyebrowActiveBridge", async () => {
    const { default: HomePage } = await import("../HomePage");
    const { getByTestId } = wrap(<HomePage />);
    expect(getByTestId("stub-eyebrow-bridge")).toBeInTheDocument();
  });

  it("mounts the FpsOverlayGate", async () => {
    const { default: HomePage } = await import("../HomePage");
    const { getByTestId } = wrap(<HomePage />);
    expect(getByTestId("stub-fps-gate")).toBeInTheDocument();
  });

  it("calls installSoundTriggers on mount", async () => {
    const { default: HomePage } = await import("../HomePage");
    wrap(<HomePage />);
    expect(installSoundTriggersMock).toHaveBeenCalled();
  });
});
