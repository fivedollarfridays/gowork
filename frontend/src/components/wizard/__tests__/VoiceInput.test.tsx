import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { VoiceInput } from "../VoiceInput";

afterEach(() => {
  // Clean up any window overrides
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  delete (window as any).SpeechRecognition;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  delete (window as any).webkitSpeechRecognition;
});

describe("VoiceInput", () => {
  it("renders the microphone button", () => {
    render(<VoiceInput onTranscript={vi.fn()} />);
    expect(screen.getByRole("button", { name: /voice/i })).toBeInTheDocument();
  });

  it("shows unsupported message when Web Speech API unavailable", () => {
    render(<VoiceInput onTranscript={vi.fn()} />);
    const btn = screen.getByRole("button", { name: /voice/i });
    fireEvent.click(btn);
    expect(screen.getByText(/not supported/i)).toBeInTheDocument();
  });

  it("calls start when Speech API is available", () => {
    const startFn = vi.fn();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).SpeechRecognition = class {
      start = startFn;
      stop = vi.fn();
      onresult = null;
      onerror = null;
      onend = null;
      continuous = false;
      interimResults = false;
      lang = "";
    };

    render(<VoiceInput onTranscript={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: /voice/i }));
    expect(startFn).toHaveBeenCalled();
  });
});
