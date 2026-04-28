/**
 * W1 Driver C — PWAInstallPrompt (Wave 7 enrichment).
 *
 * Captures the BeforeInstallPromptEvent and surfaces a discreet
 * install affordance. Renders nothing when the browser does not
 * support it (Safari iOS, Firefox, etc.).
 */
import { describe, it, expect } from "vitest";
import { act, render, screen, fireEvent } from "@testing-library/react";
import { PWAInstallPrompt } from "../PWAInstallPrompt";

interface FakePromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
  preventDefault: () => void;
}

function fireBeforeInstall() {
  const evt: Partial<FakePromptEvent> = {
    type: "beforeinstallprompt",
    prompt: () => Promise.resolve(),
    userChoice: Promise.resolve({ outcome: "accepted" }),
    preventDefault: () => {},
  };
  window.dispatchEvent(new CustomEvent("beforeinstallprompt", { detail: evt }));
}

describe("PWAInstallPrompt", () => {
  it("renders nothing when no install event has fired", () => {
    const { container } = render(<PWAInstallPrompt />);
    expect(container.textContent ?? "").toBe("");
  });

  it("renders the install affordance after beforeinstallprompt fires", () => {
    render(<PWAInstallPrompt />);
    act(() => {
      fireBeforeInstall();
    });
    expect(
      screen.getByRole("button", { name: /^install$/i }),
    ).toBeInTheDocument();
  });

  it("hides itself when dismiss is clicked", () => {
    render(<PWAInstallPrompt />);
    act(() => {
      fireBeforeInstall();
    });
    fireEvent.click(screen.getByRole("button", { name: /dismiss install/i }));
    expect(
      screen.queryByRole("button", { name: /^install$/i }),
    ).not.toBeInTheDocument();
  });
});
