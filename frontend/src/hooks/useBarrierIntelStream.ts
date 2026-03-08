"use client";

import { useCallback, useState } from "react";

import { streamBarrierIntelChat } from "@/lib/api";
import type { ChatContext, ChatMessage, ChatMode, ChatSSEEvent } from "@/lib/types";

export function useBarrierIntelStream(sessionId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [context, setContext] = useState<ChatContext | null>(null);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (question: string, mode: ChatMode = "next_steps") => {
      if (!sessionId || isStreaming) return;
      setError(null);
      setMessages((prev) => [...prev, { role: "user", content: question }]);
      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
      setIsStreaming(true);

      try {
        await streamBarrierIntelChat(sessionId, question, mode, (event: ChatSSEEvent) => {
          if (event.type === "context") {
            setContext({ root_barriers: event.root_barriers ?? [], chain: event.chain ?? "" });
          } else if (event.type === "token" && event.text) {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last?.role === "assistant") {
                updated[updated.length - 1] = { ...last, content: last.content + event.text };
              }
              return updated;
            });
          } else if (event.type === "done") {
            setIsStreaming(false);
          }
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Something went wrong");
        setIsStreaming(false);
      }
    },
    [sessionId, isStreaming],
  );

  return { messages, isStreaming, context, error, sendMessage };
}
