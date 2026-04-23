import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  render,
  screen,
  within,
  waitFor,
  fireEvent,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import type { Appointment } from "@/lib/api/appointments";
import axe from "axe-core";

// Shared mock searchParams — token and session are read from here
const mockSearchParams = new URLSearchParams();
vi.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
}));

// Mock the appointments API module — all functions are vi.fn() we control per-test
vi.mock("@/lib/api/appointments", async () => {
  return {
    listAppointments: vi.fn(),
    listUpcoming: vi.fn(),
    createAppointment: vi.fn(),
    updateAppointment: vi.fn(),
    markAttended: vi.fn(),
    markMissed: vi.fn(),
    cancelAppointment: vi.fn(),
    fromPathway: vi.fn(),
  };
});

// Avoid loading the full react-big-calendar CSS / DOM in unit tests; we render a
// minimal stand-in that still exposes events as interactive elements so that
// click behavior can be asserted.
vi.mock("react-big-calendar", async () => {
  const React = await import("react");
  type StubEvent = {
    id: number;
    title: string;
    start: Date;
    end: Date;
    resource: Appointment;
  };
  type StubProps = {
    events?: StubEvent[];
    onSelectEvent?: (event: StubEvent) => void;
  };
  function Calendar({ events = [], onSelectEvent }: StubProps) {
    return React.createElement(
      "div",
      { "data-testid": "calendar-stub", role: "grid", "aria-label": "Calendar" },
      events.map((ev) =>
        React.createElement(
          "button",
          {
            key: ev.id,
            type: "button",
            onClick: () => onSelectEvent?.(ev),
            "data-testid": `calendar-event-${ev.id}`,
          },
          ev.title,
        ),
      ),
    );
  }
  return {
    Calendar,
    dateFnsLocalizer: () => ({}),
    Views: { MONTH: "month", WEEK: "week", DAY: "day", AGENDA: "agenda" },
    default: Calendar,
  };
});

// Page under test — imported after mocks are declared
import AppointmentsPage from "@/app/appointments/page";
import * as apiMod from "@/lib/api/appointments";

const api = apiMod as unknown as {
  listAppointments: ReturnType<typeof vi.fn>;
  listUpcoming: ReturnType<typeof vi.fn>;
  createAppointment: ReturnType<typeof vi.fn>;
  updateAppointment: ReturnType<typeof vi.fn>;
  markAttended: ReturnType<typeof vi.fn>;
  markMissed: ReturnType<typeof vi.fn>;
  cancelAppointment: ReturnType<typeof vi.fn>;
  fromPathway: ReturnType<typeof vi.fn>;
};

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <TranslationProvider>
        <AppointmentsPage />
      </TranslationProvider>
    </QueryClientProvider>,
  );
}

function makeAppointment(overrides: Partial<Appointment> = {}): Appointment {
  return {
    id: 1,
    session_id: "sess-1",
    type: "interview",
    title: "Interview at Acme",
    starts_at: "2026-05-01T15:00:00Z",
    ends_at: "2026-05-01T16:00:00Z",
    location_name: "Acme HQ",
    location_address: "123 Main St",
    barrier_link: null,
    status: "scheduled",
    source: "user",
    notes: null,
    ...overrides,
  };
}

beforeEach(() => {
  setLocale("en");
  mockSearchParams.set("session", "sess-1");
  mockSearchParams.set("token", "tkn");
  sessionStorage.clear();
  vi.clearAllMocks();

  api.listAppointments.mockResolvedValue([]);
  api.listUpcoming.mockResolvedValue([]);
});

afterEach(() => {
  mockSearchParams.delete("session");
  mockSearchParams.delete("token");
});

describe("AppointmentsPage: header and tabs", () => {
  it("renders page title and tab switcher", async () => {
    renderPage();
    expect(
      await screen.findByRole("heading", { name: /appointments/i, level: 1 }),
    ).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /calendar/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /upcoming/i })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /new appointment/i }),
    ).toBeInTheDocument();
  });

  it("shows 'missing session' message when no session available", async () => {
    mockSearchParams.delete("session");
    mockSearchParams.delete("token");
    renderPage();
    expect(
      await screen.findByText(/no session available/i),
    ).toBeInTheDocument();
  });
});

describe("AppointmentsPage: list view", () => {
  it("renders AppointmentCard for each upcoming appointment", async () => {
    const items = [
      makeAppointment({ id: 1, title: "Interview A" }),
      makeAppointment({ id: 2, title: "Training B", type: "training" }),
    ];
    api.listAppointments.mockResolvedValue(items);
    api.listUpcoming.mockResolvedValue(items);
    renderPage();

    // Switch to list tab
    await userEvent.click(screen.getByRole("tab", { name: /upcoming/i }));

    expect(await screen.findByText("Interview A")).toBeInTheDocument();
    expect(await screen.findByText("Training B")).toBeInTheDocument();
  });

  it("shows empty state when no upcoming appointments", async () => {
    renderPage();
    await userEvent.click(screen.getByRole("tab", { name: /upcoming/i }));
    expect(
      await screen.findByText(/no upcoming appointments/i),
    ).toBeInTheDocument();
  });
});

describe("AppointmentsPage: calendar view", () => {
  it("renders calendar events for appointments with dates", async () => {
    api.listAppointments.mockResolvedValue([
      makeAppointment({ id: 1, title: "Interview A" }),
    ]);
    renderPage();
    // Default tab is calendar
    expect(await screen.findByTestId("calendar-stub")).toBeInTheDocument();
    expect(
      await screen.findByTestId("calendar-event-1"),
    ).toBeInTheDocument();
  });

  it("omits calendar events that have no starts_at", async () => {
    api.listAppointments.mockResolvedValue([
      makeAppointment({ id: 1, title: "Dated" }),
      makeAppointment({
        id: 2,
        title: "Placeholder",
        starts_at: null,
        ends_at: null,
        source: "pathway_auto",
      }),
    ]);
    renderPage();
    expect(await screen.findByTestId("calendar-event-1")).toBeInTheDocument();
    expect(screen.queryByTestId("calendar-event-2")).not.toBeInTheDocument();
  });
});

describe("AppointmentsPage: create flow", () => {
  it("opens modal when New appointment clicked and posts on Save", async () => {
    api.createAppointment.mockResolvedValue(
      makeAppointment({ id: 99, title: "Brand new" }),
    );
    renderPage();
    await userEvent.click(
      screen.getByRole("button", { name: /new appointment/i }),
    );

    const dialog = await screen.findByRole("dialog");
    const titleInput = within(dialog).getByLabelText(/title/i);
    fireEvent.change(titleInput, { target: { value: "Brand new" } });
    const startsInput = within(dialog).getByLabelText(/starts at/i);
    fireEvent.change(startsInput, { target: { value: "2026-06-01T10:00" } });

    await userEvent.click(within(dialog).getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(api.createAppointment).toHaveBeenCalledTimes(1);
    });
    const [payload, token] = api.createAppointment.mock.calls[0];
    expect(token).toBe("tkn");
    expect(payload).toMatchObject({ session_id: "sess-1", title: "Brand new" });
  });

  it("blocks save when title empty and shows validation", async () => {
    renderPage();
    await userEvent.click(
      screen.getByRole("button", { name: /new appointment/i }),
    );
    const dialog = await screen.findByRole("dialog");
    await userEvent.click(within(dialog).getByRole("button", { name: /save/i }));
    expect(
      within(dialog).getByText(/title is required/i),
    ).toBeInTheDocument();
    expect(api.createAppointment).not.toHaveBeenCalled();
  });
});

describe("AppointmentsPage: edit flow", () => {
  it("opens modal pre-filled when card is clicked and PATCHes on save", async () => {
    api.listAppointments.mockResolvedValue([
      makeAppointment({ id: 7, title: "Original" }),
    ]);
    api.listUpcoming.mockResolvedValue([
      makeAppointment({ id: 7, title: "Original" }),
    ]);
    api.updateAppointment.mockResolvedValue(
      makeAppointment({ id: 7, title: "Updated" }),
    );
    renderPage();

    await userEvent.click(screen.getByRole("tab", { name: /upcoming/i }));
    await userEvent.click(
      await screen.findByRole("button", { name: /edit appointment: original/i }),
    );
    const dialog = await screen.findByRole("dialog");
    const titleInput = within(dialog).getByLabelText(/title/i) as HTMLInputElement;
    expect(titleInput.value).toBe("Original");
    fireEvent.change(titleInput, { target: { value: "Updated" } });
    await userEvent.click(within(dialog).getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(api.updateAppointment).toHaveBeenCalledTimes(1);
    });
    const [id, changes, token] = api.updateAppointment.mock.calls[0];
    expect(id).toBe(7);
    expect(token).toBe("tkn");
    expect(changes).toMatchObject({ title: "Updated" });
  });
});

describe("AppointmentsPage: status action buttons", () => {
  it("mark attended calls markAttended API", async () => {
    api.listAppointments.mockResolvedValue([makeAppointment({ id: 5 })]);
    api.listUpcoming.mockResolvedValue([makeAppointment({ id: 5 })]);
    api.markAttended.mockResolvedValue(
      makeAppointment({ id: 5, status: "attended" }),
    );
    renderPage();
    await userEvent.click(screen.getByRole("tab", { name: /upcoming/i }));
    await userEvent.click(
      await screen.findByRole("button", { name: /mark attended/i }),
    );
    await waitFor(() => {
      expect(api.markAttended).toHaveBeenCalledWith(5, "tkn");
    });
  });

  it("mark missed calls markMissed API", async () => {
    api.listAppointments.mockResolvedValue([makeAppointment({ id: 6 })]);
    api.listUpcoming.mockResolvedValue([makeAppointment({ id: 6 })]);
    api.markMissed.mockResolvedValue(
      makeAppointment({ id: 6, status: "missed" }),
    );
    renderPage();
    await userEvent.click(screen.getByRole("tab", { name: /upcoming/i }));
    await userEvent.click(
      await screen.findByRole("button", { name: /mark missed/i }),
    );
    await waitFor(() => {
      expect(api.markMissed).toHaveBeenCalledWith(6, "tkn");
    });
  });

  it("cancel calls cancelAppointment API", async () => {
    api.listAppointments.mockResolvedValue([makeAppointment({ id: 8 })]);
    api.listUpcoming.mockResolvedValue([makeAppointment({ id: 8 })]);
    api.cancelAppointment.mockResolvedValue(
      makeAppointment({ id: 8, status: "cancelled" }),
    );
    renderPage();
    await userEvent.click(screen.getByRole("tab", { name: /upcoming/i }));
    await userEvent.click(
      await screen.findByRole("button", { name: /^cancel:/i }),
    );
    await waitFor(() => {
      expect(api.cancelAppointment).toHaveBeenCalledWith(8, "tkn");
    });
  });
});

describe("AppointmentsPage: placeholder prompts", () => {
  it("shows banner when pathway_auto placeholders without starts_at exist", async () => {
    api.listAppointments.mockResolvedValue([
      makeAppointment({
        id: 10,
        title: "Credit coach meeting",
        starts_at: null,
        ends_at: null,
        source: "pathway_auto",
      }),
      makeAppointment({
        id: 11,
        title: "Housing intake",
        starts_at: null,
        ends_at: null,
        source: "pathway_auto",
      }),
    ]);
    renderPage();
    const banner = await screen.findByRole("region", { name: /placeholder/i });
    expect(banner).toBeInTheDocument();
    expect(within(banner).getByText(/2/)).toBeInTheDocument();
  });

  it("placeholder Schedule button opens modal with prefilled title", async () => {
    api.listAppointments.mockResolvedValue([
      makeAppointment({
        id: 20,
        title: "Credit coach meeting",
        type: "appointment",
        starts_at: null,
        ends_at: null,
        source: "pathway_auto",
        barrier_link: "credit",
      }),
    ]);
    api.updateAppointment.mockResolvedValue(
      makeAppointment({ id: 20, title: "Credit coach meeting" }),
    );
    renderPage();
    await userEvent.click(
      await screen.findByRole("button", { name: /schedule.*credit coach/i }),
    );
    const dialog = await screen.findByRole("dialog");
    const titleInput = within(dialog).getByLabelText(/title/i) as HTMLInputElement;
    expect(titleInput.value).toBe("Credit coach meeting");
  });
});

describe("AppointmentsPage: a11y", () => {
  it("is free of axe-core violations", async () => {
    api.listAppointments.mockResolvedValue([
      makeAppointment({ id: 1, title: "Interview" }),
    ]);
    api.listUpcoming.mockResolvedValue([
      makeAppointment({ id: 1, title: "Interview" }),
    ]);
    const { container } = renderPage();
    // Wait for data
    await screen.findByRole("heading", { name: /appointments/i, level: 1 });

    const results = await axe.run(container, {
      // Exclude color-contrast since jsdom doesn't compute styles
      rules: { "color-contrast": { enabled: false } },
    });
    expect(results.violations).toEqual([]);
  });

  it("action buttons are keyboard focusable", async () => {
    api.listAppointments.mockResolvedValue([makeAppointment({ id: 1 })]);
    api.listUpcoming.mockResolvedValue([makeAppointment({ id: 1 })]);
    renderPage();
    await userEvent.click(screen.getByRole("tab", { name: /upcoming/i }));
    const attended = await screen.findByRole("button", {
      name: /mark attended/i,
    });
    attended.focus();
    expect(attended).toHaveFocus();
  });
});
