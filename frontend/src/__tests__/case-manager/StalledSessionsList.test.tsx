import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { StalledSessionsList } from "@/components/StalledSessionsList";
import type { AdvisorStalledSession } from "@/lib/api/advisor";

function renderList(props: React.ComponentProps<typeof StalledSessionsList>) {
  return render(
    <TranslationProvider>
      <StalledSessionsList {...props} />
    </TranslationProvider>,
  );
}

describe("StalledSessionsList", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("renders an empty state when there are no sessions", () => {
    renderList({ sessions: [], onSelect: () => {} });
    expect(
      screen.getByText(/no sessions need attention/i),
    ).toBeInTheDocument();
  });

  it("renders each session with severity + days stalled", () => {
    const sessions: AdvisorStalledSession[] = [
      {
        session_id: "sess-1",
        city: "montgomery",
        stall_level: "hard",
        days_stalled: 20,
      },
      {
        session_id: "sess-2",
        city: "montgomery",
        stall_level: "medium",
        days_stalled: 10,
      },
    ];
    renderList({ sessions, onSelect: () => {} });
    expect(screen.getByText("sess-1")).toBeInTheDocument();
    expect(screen.getByText("sess-2")).toBeInTheDocument();
    expect(screen.getByText(/20 days/i)).toBeInTheDocument();
    expect(screen.getByText(/10 days/i)).toBeInTheDocument();
    expect(screen.getByText(/hard/i)).toBeInTheDocument();
    expect(screen.getByText(/medium/i)).toBeInTheDocument();
  });

  it("preserves the severity sort order provided by the backend", () => {
    const sessions: AdvisorStalledSession[] = [
      { session_id: "a", city: "m", stall_level: "hard", days_stalled: 30 },
      { session_id: "b", city: "m", stall_level: "hard", days_stalled: 20 },
      { session_id: "c", city: "m", stall_level: "medium", days_stalled: 10 },
      { session_id: "d", city: "m", stall_level: "soft", days_stalled: 4 },
    ];
    renderList({ sessions, onSelect: () => {} });
    const items = screen.getAllByTestId("stalled-session-row");
    expect(items[0]).toHaveTextContent("a");
    expect(items[1]).toHaveTextContent("b");
    expect(items[2]).toHaveTextContent("c");
    expect(items[3]).toHaveTextContent("d");
  });

  it("calls onSelect with the session id when a row is clicked", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    renderList({
      sessions: [
        {
          session_id: "sess-x", city: "m",
          stall_level: "hard", days_stalled: 20,
        },
      ],
      onSelect,
    });
    await user.click(screen.getByRole("button", { name: /sess-x/i }));
    expect(onSelect).toHaveBeenCalledWith("sess-x");
  });

  it("shows a visual severity indicator for hard stalls", () => {
    renderList({
      sessions: [
        {
          session_id: "hot", city: "m",
          stall_level: "hard", days_stalled: 20,
        },
      ],
      onSelect: () => {},
    });
    const badge = screen.getByTestId("stall-badge-hot");
    expect(badge).toHaveAttribute("data-stall-level", "hard");
  });
});
