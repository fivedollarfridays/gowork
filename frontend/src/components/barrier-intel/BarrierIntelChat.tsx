"use client";

import { useRef, useState } from "react";
import { MessageSquare, Send, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useBarrierIntelStream } from "@/hooks/useBarrierIntelStream";

import { ChatMessage } from "./ChatMessage";
import { SuggestedQuestions } from "./SuggestedQuestions";

interface BarrierIntelChatProps {
  sessionId: string | null;
}

export function BarrierIntelChat({ sessionId }: BarrierIntelChatProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const { messages, isStreaming, error, sendMessage } = useBarrierIntelStream(sessionId);
  const scrollRef = useRef<HTMLDivElement>(null);

  const handleSend = () => {
    const q = input.trim();
    if (!q) return;
    setInput("");
    sendMessage(q);
    setTimeout(() => scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight }), 100);
  };

  const handleSuggestion = (question: string) => {
    sendMessage(question);
    setTimeout(() => scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight }), 100);
  };

  if (!sessionId) return null;

  // Mobile: floating button + drawer
  if (!isOpen) {
    return (
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 z-50 flex items-center gap-2 rounded-full bg-primary px-4 py-3 text-sm font-medium text-primary-foreground shadow-lg transition-transform hover:scale-105 lg:hidden"
        aria-label="Ask about your plan"
      >
        <MessageSquare className="h-5 w-5" />
        Ask about your plan
      </button>
    );
  }

  const chatPanel = (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h3 className="text-sm font-semibold">Barrier Intelligence Assistant</h3>
        <button
          type="button"
          onClick={() => setIsOpen(false)}
          className="lg:hidden"
          aria-label="Close chat"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {messages.length === 0 && (
        <div className="px-4 pt-4">
          <p className="mb-3 text-xs text-muted-foreground">Try asking:</p>
          <SuggestedQuestions onSelect={handleSuggestion} disabled={isStreaming} />
        </div>
      )}

      <ScrollArea className="flex-1 px-4 py-2" ref={scrollRef}>
        <div className="space-y-3">
          {messages.map((msg, i) => (
            <ChatMessage
              key={i}
              message={msg}
              isStreaming={isStreaming && i === messages.length - 1 && msg.role === "assistant"}
            />
          ))}
        </div>
      </ScrollArea>

      {error && <p className="px-4 text-xs text-destructive">{error}</p>}

      <div className="border-t px-4 py-3">
        {messages.length > 0 && (
          <div className="mb-2">
            <SuggestedQuestions onSelect={handleSuggestion} disabled={isStreaming} />
          </div>
        )}
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            placeholder="Ask about your plan..."
            disabled={isStreaming}
            className="flex-1"
          />
          <Button onClick={handleSend} disabled={isStreaming || !input.trim()} size="icon">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop: sidebar */}
      <div className="hidden lg:block lg:w-80 lg:border-l lg:bg-card">{chatPanel}</div>
      {/* Mobile: bottom drawer */}
      <div className="fixed inset-0 z-50 flex flex-col bg-background lg:hidden">
        {chatPanel}
      </div>
    </>
  );
}
