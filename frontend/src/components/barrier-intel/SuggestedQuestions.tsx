const DEFAULT_QUESTIONS = [
  "What should I do first to find a job?",
  "Why was this plan recommended for me?",
  "What's blocking me the most right now?",
];

interface SuggestedQuestionsProps {
  onSelect: (question: string) => void;
  questions?: string[];
}

export function SuggestedQuestions({
  onSelect,
  questions = DEFAULT_QUESTIONS,
}: SuggestedQuestionsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {questions.map((q) => (
        <button
          key={q}
          onClick={() => onSelect(q)}
          className="rounded-full border border-border bg-muted px-3 py-1 text-sm hover:bg-accent"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
