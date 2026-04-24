import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TranslationProvider } from "@/hooks/useTranslation";
import { setLocale } from "@/lib/i18n";
import { SendAdvisorNoteDialog } from "@/components/SendAdvisorNoteDialog";

function renderDialog(
  props: React.ComponentProps<typeof SendAdvisorNoteDialog>,
) {
  return render(
    <TranslationProvider>
      <SendAdvisorNoteDialog {...props} />
    </TranslationProvider>,
  );
}

describe("SendAdvisorNoteDialog", () => {
  beforeEach(() => {
    setLocale("en");
  });

  it("does not render when closed", () => {
    renderDialog({
      open: false, sessionId: "s", onClose: () => {},
      onSubmit: async () => {},
    });
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("renders a textarea and submit button when open", () => {
    renderDialog({
      open: true, sessionId: "s", onClose: () => {},
      onSubmit: async () => {},
    });
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /send/i }),
    ).toBeInTheDocument();
  });

  it("disables submit when the message is empty or whitespace", async () => {
    const user = userEvent.setup();
    renderDialog({
      open: true, sessionId: "s", onClose: () => {},
      onSubmit: async () => {},
    });
    const btn = screen.getByRole("button", { name: /send/i });
    expect(btn).toBeDisabled();
    await user.type(screen.getByRole("textbox"), "   ");
    expect(btn).toBeDisabled();
  });

  it("calls onSubmit with the typed message", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    renderDialog({
      open: true, sessionId: "sess-42", onClose: () => {},
      onSubmit,
    });
    await user.type(
      screen.getByRole("textbox"),
      "Hey, give me a call this week.",
    );
    await user.click(screen.getByRole("button", { name: /send/i }));
    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        "Hey, give me a call this week.",
      );
    });
  });

  it("surfaces a rate-limit error message on 429", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockRejectedValue(
      Object.assign(new Error("Rate limit"), { status: 429 }),
    );
    renderDialog({
      open: true, sessionId: "s", onClose: () => {}, onSubmit,
    });
    await user.type(screen.getByRole("textbox"), "hello");
    await user.click(screen.getByRole("button", { name: /send/i }));
    await waitFor(() => {
      expect(
        screen.getByText(/rate.limit|too many/i),
      ).toBeInTheDocument();
    });
  });

  it("surfaces a 403 error message with a clear description", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockRejectedValue(
      Object.assign(new Error("Cross-city access denied"), { status: 403 }),
    );
    renderDialog({
      open: true, sessionId: "s", onClose: () => {}, onSubmit,
    });
    await user.type(screen.getByRole("textbox"), "hi");
    await user.click(screen.getByRole("button", { name: /send/i }));
    await waitFor(() => {
      expect(
        screen.getByText(/access denied|not available/i),
      ).toBeInTheDocument();
    });
  });
});
