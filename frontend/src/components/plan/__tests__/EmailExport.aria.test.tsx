import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { EmailExport } from "../EmailExport";

// Mock env vars for EmailJS
beforeEach(() => {
  process.env.NEXT_PUBLIC_EMAILJS_SERVICE_ID = "svc-test";
  process.env.NEXT_PUBLIC_EMAILJS_TEMPLATE_ID = "tmpl-test";
  process.env.NEXT_PUBLIC_EMAILJS_PUBLIC_KEY = "key-test";
});

describe("EmailExport data minimization", () => {
  it("template params contain plan URL instead of PII", async () => {
    let capturedParams: Record<string, string> = {};

    vi.doMock("@emailjs/browser", () => ({
      default: {
        send: vi.fn((_svc: string, _tmpl: string, params: Record<string, string>) => {
          capturedParams = params;
          return Promise.resolve();
        }),
      },
    }));

    render(<EmailExport sessionId="sess-123" token="tok-abc" />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /email my plan/i }));
    const input = screen.getByPlaceholderText("your@email.com");
    await user.type(input, "test@example.com");
    await user.click(screen.getByRole("button", { name: /send/i }));
    await screen.findByText(/plan sent to/i);

    // Should NOT contain PII
    expect(capturedParams.barrier_list).toBeUndefined();
    expect(capturedParams.job_list).toBeUndefined();
    expect(capturedParams.next_steps).toBeUndefined();
    expect(capturedParams.plan_summary).toBeUndefined();

    // Should contain plan URL with session and token
    expect(capturedParams.plan_url).toContain("session=sess-123");
    expect(capturedParams.plan_url).toContain("token=tok-abc");
    expect(capturedParams.to_email).toBe("test@example.com");

    vi.doUnmock("@emailjs/browser");
  });

  it("summary is a generic message without sensitive data", async () => {
    let capturedParams: Record<string, string> = {};

    vi.doMock("@emailjs/browser", () => ({
      default: {
        send: vi.fn((_svc: string, _tmpl: string, params: Record<string, string>) => {
          capturedParams = params;
          return Promise.resolve();
        }),
      },
    }));

    render(<EmailExport sessionId="sess-123" token="tok-abc" />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /email my plan/i }));
    const input = screen.getByPlaceholderText("your@email.com");
    await user.type(input, "test@example.com");
    await user.click(screen.getByRole("button", { name: /send/i }));
    await screen.findByText(/plan sent to/i);

    expect(capturedParams.summary).toBeDefined();
    expect(capturedParams.summary).not.toContain("credit");
    expect(capturedParams.summary).not.toContain("barrier");

    vi.doUnmock("@emailjs/browser");
  });
});

describe("EmailExport ARIA attributes", () => {
  it("error message has role=alert", async () => {
    vi.doMock("@emailjs/browser", () => ({
      default: {
        send: vi.fn(() => Promise.reject(new Error("Send failed"))),
      },
    }));

    render(<EmailExport sessionId="sess-abc" token="tok-t" />);
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: /email my plan/i }));
    const input = screen.getByPlaceholderText("your@email.com");
    await user.type(input, "test@example.com");
    await user.click(screen.getByRole("button", { name: /send/i }));

    const alert = await screen.findByRole("alert");
    expect(alert).toBeInTheDocument();

    vi.doUnmock("@emailjs/browser");
  });

  it("success message has aria-live=polite", async () => {
    vi.doMock("@emailjs/browser", () => ({
      default: {
        send: vi.fn(() => Promise.resolve()),
      },
    }));

    render(<EmailExport sessionId="sess-abc" token="tok-t" />);
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: /email my plan/i }));
    const input = screen.getByPlaceholderText("your@email.com");
    await user.type(input, "test@example.com");
    await user.click(screen.getByRole("button", { name: /send/i }));

    const successDiv = await screen.findByText(/plan sent to/i);
    expect(successDiv.closest("[aria-live]")).toHaveAttribute("aria-live", "polite");

    vi.doUnmock("@emailjs/browser");
  });
});
