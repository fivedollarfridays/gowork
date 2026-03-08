"use client";

const SUGGESTIONS = [
  "What should I do first to find a job?",
  "Why was this plan recommended for me?",
  "What's blocking me the most right now?",
];

interface SuggestedQuestionsProps {
  onSelect: (question: string) => void;
  disabled?: boolean;
}

export function SuggestedQuestions({ onSelect, disabled }: SuggestedQuestionsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {SUGGESTIONS.map((q) => (
        <button
          key={q}
          type="button"
          onClick={() => onSelect(q)}
          disabled={disabled}
          className="rounded-full border border-input bg-background px-3 py-1 text-xs text-muted-foreground transition-colors hover:bg-muted disabled:opacity-50"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
