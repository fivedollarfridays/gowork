import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CareerCenterExport } from "../CareerCenterExport";

// Mock the API module
vi.mock("@/lib/api", () => ({
  getCareerCenterPackage: vi.fn(),
}));

import { getCareerCenterPackage } from "@/lib/api";
import type { CareerCenterPackage } from "@/lib/types";

const mockPackage: CareerCenterPackage = {
  staff_summary: {
    employment_goal: "Employment for unemployed resident",
    barrier_profile: ["credit", "transportation"],
    wioa_eligibility: {
      adult_program: true,
      adult_reasons: ["credit"],
      supportive_services: true,
      ita_training: false,
      dislocated_worker: "needs_verification",
      confidence: "likely",
    },
    staff_next_steps: ["Visit Career Center"],
  },
  resident_plan: {
    document_checklist: [
      { label: "Government-issued photo ID", required: true },
    ],
    work_history: "Former CNA",
    what_to_say: ["I need help finding work."],
    what_to_expect: ["Initial intake"],
    career_center: {
      name: "Montgomery Career Center",
      phone: "334-286-1746",
      address: "1060 East South Blvd",
      hours: "Mon-Fri 8am-5pm",
      transit_route: "Route 6",
    },
    programs: ["WIOA Adult Program"],
  },
  credit_pathway: null,
  generated_at: "2026-03-06T12:00:00Z",
};

const mockedGet = vi.mocked(getCareerCenterPackage);

describe("CareerCenterExport", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders a Career Center PDF button", () => {
    render(<CareerCenterExport sessionId="sess-1" />);
    const button = screen.getByRole("button", { name: /career center pdf/i });
    expect(button).toBeInTheDocument();
  });

  it("fetches career center package on click", async () => {
    mockedGet.mockResolvedValue(mockPackage);
    // Mock html2pdf
    vi.doMock("html2pdf.js", () => ({
      default: () => ({
        set: vi.fn().mockReturnThis(),
        from: vi.fn().mockReturnThis(),
        save: vi.fn(() => Promise.resolve()),
      }),
    }));

    render(<CareerCenterExport sessionId="sess-1" />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /career center pdf/i }));

    expect(mockedGet).toHaveBeenCalledWith("sess-1");
    vi.doUnmock("html2pdf.js");
  });

  it("shows loading state while generating", async () => {
    let resolveSave!: () => void;
    const savePromise = new Promise<void>((r) => { resolveSave = r; });
    mockedGet.mockResolvedValue(mockPackage);
    vi.doMock("html2pdf.js", () => ({
      default: () => ({
        set: vi.fn().mockReturnThis(),
        from: vi.fn().mockReturnThis(),
        save: vi.fn(() => savePromise),
      }),
    }));

    render(<CareerCenterExport sessionId="sess-1" />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /career center pdf/i }));

    await waitFor(() => {
      expect(screen.getByText(/generating/i)).toBeInTheDocument();
    });
    const button = screen.getByRole("button");
    expect(button).toBeDisabled();

    resolveSave();
    vi.doUnmock("html2pdf.js");
  });

  it("shows error on API failure", async () => {
    mockedGet.mockRejectedValue(new Error("Network error"));

    render(<CareerCenterExport sessionId="sess-1" />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /career center pdf/i }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/failed/i);
  });

  it("shows error on html2pdf failure", async () => {
    mockedGet.mockResolvedValue(mockPackage);
    vi.doMock("html2pdf.js", () => ({
      default: () => ({
        set: vi.fn().mockReturnThis(),
        from: vi.fn().mockReturnThis(),
        save: vi.fn(() => Promise.reject(new Error("PDF failed"))),
      }),
    }));

    render(<CareerCenterExport sessionId="sess-1" />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /career center pdf/i }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/failed/i);

    vi.doUnmock("html2pdf.js");
  });

  it("button has aria-label during generation", async () => {
    let resolveSave!: () => void;
    const savePromise = new Promise<void>((r) => { resolveSave = r; });
    mockedGet.mockResolvedValue(mockPackage);
    vi.doMock("html2pdf.js", () => ({
      default: () => ({
        set: vi.fn().mockReturnThis(),
        from: vi.fn().mockReturnThis(),
        save: vi.fn(() => savePromise),
      }),
    }));

    render(<CareerCenterExport sessionId="sess-1" />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /career center pdf/i }));

    await waitFor(() => {
      const btn = screen.getByRole("button");
      expect(btn).toHaveAttribute("aria-label", "Generating PDF, please wait");
    });

    resolveSave();
    vi.doUnmock("html2pdf.js");
  });

  it("renders CareerCenterPrintLayout offscreen after fetch", async () => {
    mockedGet.mockResolvedValue(mockPackage);
    vi.doMock("html2pdf.js", () => ({
      default: () => ({
        set: vi.fn().mockReturnThis(),
        from: vi.fn().mockReturnThis(),
        save: vi.fn(() => Promise.resolve()),
      }),
    }));

    render(<CareerCenterExport sessionId="sess-1" />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /career center pdf/i }));

    await waitFor(() => {
      expect(screen.getByText(/Montgomery Career Center/)).toBeInTheDocument();
    });

    vi.doUnmock("html2pdf.js");
  });
});
