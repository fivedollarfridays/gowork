import { useRef, useState } from "react";
import { useBarrierIntelStream } from "@/hooks/useBarrierIntelStream";
import { ChatMessage } from "./ChatMessage";
import { SuggestedQuestions } from "./SuggestedQuestions";
import { EvidenceChips } from "./EvidenceChips";

interface BarrierIntelChatProps {
  sessionId: string;
  sources?: string[];
}

export function BarrierIntelChat({ sessionId, sources = [] }: BarrierIntelChatProps) {
  const [input, setInput] = useState("");
  const { messages, status, sendQuestion } = useBarrierIntelStream();
  const formRef = useRef<HTMLFormElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = input.trim();
    if (!q || status === "streaming") return;
    setInput("");
    sendQuestion(sessionId, q);
  };

  const handleSelect = (q: string) => {
    setInput(q);
    sendQuestion(sessionId, q);
  };

  const handleExplainPlan = () => {
    sendQuestion(sessionId, "Explain this plan to me", "explain_plan");
  };

  return (
    <div className="flex flex-col gap-3">
      {messages.length === 0 && (
        <>
          <button
            onClick={handleExplainPlan}
            disabled={status === "streaming"}
            className="rounded border border-primary px-3 py-1.5 text-sm font-medium text-primary hover:bg-primary/10 disabled:opacity-50"
          >
            Explain this plan
          </button>
          <SuggestedQuestions onSelect={handleSelect} />
        </>
      )}

      <div className="flex flex-col gap-2">
        {messages.map((m, i) => (
          <ChatMessage
            key={i}
            role={m.role}
            text={m.text}
            isError={m.isError}
            isStreaming={status === "streaming" && i === messages.length - 1 && m.role === "assistant"}
          />
        ))}
      </div>

      {sources.length > 0 && <EvidenceChips sources={sources} />}

      {status === "error" && (
        <p role="alert" className="text-sm text-destructive">
          Something went wrong. Please try again.
        </p>
      )}

      <form ref={formRef} onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your plan…"
          disabled={status === "streaming"}
          className="flex-1 rounded border border-border bg-background px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={!input.trim() || status === "streaming"}
          className="rounded bg-primary px-3 py-2 text-sm text-primary-foreground disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
