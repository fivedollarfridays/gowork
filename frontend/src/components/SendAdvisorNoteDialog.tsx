"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTranslation } from "@/hooks/useTranslation";

export interface SendAdvisorNoteDialogProps {
  open: boolean;
  sessionId: string;
  onClose: () => void;
  onSubmit: (message: string) => Promise<void>;
}

interface ErrorWithStatus extends Error {
  status?: number;
}

function errorKey(err: unknown): string {
  const e = err as ErrorWithStatus;
  if (e?.status === 429) return "advisor.noteRateLimited";
  if (e?.status === 403) return "advisor.noteForbidden";
  return "advisor.noteGenericError";
}

export function SendAdvisorNoteDialog({
  open, sessionId, onClose, onSubmit,
}: SendAdvisorNoteDialogProps) {
  const { t } = useTranslation();
  const [message, setMessage] = useState("");
  const [errorText, setErrorText] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (!open) {
      setMessage("");
      setErrorText(null);
      setSending(false);
    }
  }, [open]);

  if (!open) return null;

  const trimmed = message.trim();
  const canSubmit = trimmed.length > 0 && !sending;

  async function handleSubmit(): Promise<void> {
    if (!canSubmit) return;
    setSending(true);
    setErrorText(null);
    try {
      await onSubmit(trimmed);
      setMessage("");
      onClose();
    } catch (err) {
      setErrorText(t(errorKey(err)));
    } finally {
      setSending(false);
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="advisor-note-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4"
    >
      <div className="w-full max-w-lg rounded-lg border bg-card p-6 shadow-lg">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <h2
              id="advisor-note-title"
              className="text-lg font-semibold"
            >
              {t("advisor.noteDialogTitle")}
            </h2>
            <p className="text-sm text-muted-foreground">
              {t("advisor.noteDialogDescription")}
            </p>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onClose}
            aria-label={t("advisor.noteCancel")}
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </Button>
        </div>
        <form
          className="mt-4 space-y-3"
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit();
          }}
        >
          <label className="block text-sm font-medium">
            <span className="sr-only">{t("advisor.noteLabel")}</span>
            <textarea
              className="w-full min-h-[120px] rounded-md border bg-background p-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder={t("advisor.notePlaceholder")}
              maxLength={2000}
              aria-label={`${t("advisor.noteLabel")} — ${sessionId}`}
            />
          </label>
          {errorText && (
            <p role="alert" className="text-sm text-destructive">
              {errorText}
            </p>
          )}
          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={sending}
            >
              {t("advisor.noteCancel")}
            </Button>
            <Button type="submit" disabled={!canSubmit}>
              {t("advisor.noteSubmit")}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
