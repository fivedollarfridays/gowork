interface ChatMessageProps {
  role: "user" | "assistant";
  text: string;
  isStreaming?: boolean;
  isError?: boolean;
}

export function ChatMessage({ role, text, isStreaming, isError }: ChatMessageProps) {
  return (
    <div className={`flex gap-2 ${role === "user" ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
          isError
            ? "bg-destructive/10 text-destructive"
            : role === "user"
            ? "bg-primary text-primary-foreground"
            : "bg-muted"
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
