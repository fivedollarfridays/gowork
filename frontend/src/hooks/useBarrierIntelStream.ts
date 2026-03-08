import { useState } from "react";

export interface ChatMsg {
  role: "user" | "assistant";
  text: string;
  isError?: boolean;
}

type Status = "idle" | "streaming" | "done" | "error";

interface StreamHook {
  messages: ChatMsg[];
  status: Status;
  sendQuestion: (sessionId: string, question: string, mode?: string) => Promise<void>;
  reset: () => void;
}

export function useBarrierIntelStream(): StreamHook {
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [status, setStatus] = useState<Status>("idle");

  const sendQuestion = async (
    sessionId: string,
    question: string,
    mode = "next_steps",
  ) => {
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setStatus("streaming");
    let assistantText = "";

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_BASE}/api/barrier-intel/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, user_question: question, mode }),
      });

      if (!res.ok || !res.body) throw new Error("Request failed");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        for (const line of chunk.split("\n")) {
          if (!line.startsWith("data: ")) continue;
          const payload = JSON.parse(line.slice(6));
          if (payload.type === "token") {
            assistantText += payload.text;
            setMessages((prev) => {
              const msgs = [...prev];
              const last = msgs[msgs.length - 1];
              if (last?.role === "assistant") {
                msgs[msgs.length - 1] = { role: "assistant", text: assistantText };
              } else {
                msgs.push({ role: "assistant", text: assistantText });
              }
              return msgs;
            });
          } else if (payload.type === "error") {
            setMessages((prev) => [
              ...prev,
              { role: "assistant", text: payload.message, isError: true },
            ]);
            setStatus("error");
          } else if (payload.type === "done") {
            setStatus("done");
          }
        }
      }
    } catch {
      setStatus("error");
    }
  };

  const reset = () => {
    setMessages([]);
    setStatus("idle");
  };

  return { messages, status, sendQuestion, reset };
}
