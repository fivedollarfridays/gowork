import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { EmailExport } from "../EmailExport";
import type { ReEntryPlan } from "@/lib/types";

const basePlan: ReEntryPlan = {
  plan_id: "plan-001",
  session_id: "sess-abc",
  resident_summary: "Your path forward.",
  barriers: [],
  job_matches: [],
  immediate_next_steps: ["Step 1"],
  credit_readiness_score: null,
  eligible_now: [],
  eligible_after_repair: [],
};

// Mock env vars for EmailJS
const originalEnv = { ...process.env };

beforeEach(() => {
  process.env.NEXT_PUBLIC_EMAILJS_SERVICE_ID = "svc-test";
  process.env.NEXT_PUBLIC_EMAILJS_TEMPLATE_ID = "tmpl-test";
  process.env.NEXT_PUBLIC_EMAILJS_PUBLIC_KEY = "key-test";
});

describe("EmailExport ARIA attributes", () => {
  it("error message has role=alert", async () => {
    // Mock emailjs to reject
    vi.doMock("@emailjs/browser", () => ({
      default: {
        send: vi.fn(() => Promise.reject(new Error("Send failed"))),
      },
    }));

    render(<EmailExport plan={basePlan} />);
    const user = userEvent.setup();

    // Open the form
    await user.click(screen.getByRole("button", { name: /email my plan/i }));

    // Enter an email and send
    const input = screen.getByPlaceholderText("your@email.com");
    await user.type(input, "test@example.com");
    await user.click(screen.getByRole("button", { name: /send/i }));

    // Error should have role="alert"
    const alert = await screen.findByRole("alert");
    expect(alert).toBeInTheDocument();

    vi.doUnmock("@emailjs/browser");
  });

  it("success message has aria-live=polite", async () => {
    // Mock emailjs to succeed
    vi.doMock("@emailjs/browser", () => ({
      default: {
        send: vi.fn(() => Promise.resolve()),
      },
    }));

    render(<EmailExport plan={basePlan} />);
    const user = userEvent.setup();

    // Open the form
    await user.click(screen.getByRole("button", { name: /email my plan/i }));

    // Enter an email and send
    const input = screen.getByPlaceholderText("your@email.com");
    await user.type(input, "test@example.com");
    await user.click(screen.getByRole("button", { name: /send/i }));

    // Wait for success and check aria-live
    const successDiv = await screen.findByText(/plan sent to/i);
    expect(successDiv.closest("[aria-live]")).toHaveAttribute("aria-live", "polite");

    vi.doUnmock("@emailjs/browser");
  });
});
