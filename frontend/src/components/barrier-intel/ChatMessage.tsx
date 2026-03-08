interface ChatMessageProps {
  role: "user" | "assistant";
  text: string;
  isStreaming?: boolean;
}

export function ChatMessage({ role, text, isStreaming }: ChatMessageProps) {
  return (
    <div className={`flex gap-2 ${role === "user" ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
          role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
        }`}
      >
        {text}
        {isStreaming && (
          <span data-testid="streaming-indicator" className="ml-1 animate-pulse">
            ▋
          </span>
        )}
      </div>
    </div>
  );
}
