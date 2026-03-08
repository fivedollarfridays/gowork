"use client";

import type { ChatMessage as ChatMessageType } from "@/lib/types";

interface ChatMessageProps {
  message: ChatMessageType;
  isStreaming?: boolean;
}

export function ChatMessage({ message, isStreaming }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
          isUser ? "bg-primary text-primary-foreground" : "bg-muted text-foreground"
        }`}
      >
        <div className="whitespace-pre-wrap">{message.content}</div>
        {isStreaming && !message.content && (
          <span className="inline-block h-4 w-4 animate-pulse rounded-full bg-current opacity-40" />
        )}
      </div>
    </div>
  );
}
