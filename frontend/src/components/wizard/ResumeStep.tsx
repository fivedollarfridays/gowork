"use client";

import { useCallback, useState } from "react";
import { FileText, Loader2, Upload, X, CheckCircle2, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { extractResumeText } from "@/lib/resume";
import type { ExtractionResult } from "@/lib/resume";

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
const ACCEPTED_TYPES = ".pdf,.docx,.txt";

interface ResumeStepProps {
  resumeText: string;
  onResumeTextChange: (text: string) => void;
}

type UploadState = "idle" | "extracting" | "success" | "error";

export function ResumeStep({ resumeText, onResumeTextChange }: ResumeStepProps) {
  const [state, setState] = useState<UploadState>(resumeText ? "success" : "idle");
  const [fileName, setFileName] = useState<string>("");
  const [result, setResult] = useState<ExtractionResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [dragOver, setDragOver] = useState(false);

  const processFile = useCallback(async (file: File) => {
    if (file.size > MAX_FILE_SIZE) {
      setErrorMsg("File is too large. Maximum size is 5MB.");
      setState("error");
      return;
    }

    setFileName(file.name);
    setState("extracting");
    setErrorMsg("");

    try {
      const extraction = await extractResumeText(file);
      if (extraction.wordCount === 0) {
        setErrorMsg("Could not extract text from this file. Try a different format.");
        setState("error");
        return;
      }
      setResult(extraction);
      onResumeTextChange(extraction.text);
      setState("success");
    } catch {
      setErrorMsg("Failed to process file. Please try again.");
      setState("error");
    }
  }, [onResumeTextChange]);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
  }, [processFile]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) processFile(file);
  }, [processFile]);

  const handleClear = useCallback(() => {
    setState("idle");
    setFileName("");
    setResult(null);
    setErrorMsg("");
    onResumeTextChange("");
  }, [onResumeTextChange]);

  return (
    <div className="space-y-4">
      {state === "idle" && (
        <Card
          className={cn(
            "border-dashed border-2 p-8 text-center cursor-pointer transition-colors",
            dragOver ? "border-secondary bg-secondary/5" : "hover:border-muted-foreground/30"
          )}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => document.getElementById("resume-input")?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              document.getElementById("resume-input")?.click();
            }
          }}
        >
          <div className="flex flex-col items-center gap-3">
            <Upload className="h-8 w-8 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium">Drop your resume here or click to browse</p>
              <p className="text-xs text-muted-foreground mt-1">PDF, DOCX, or TXT (max 5MB)</p>
            </div>
          </div>
          <input
            id="resume-input"
            type="file"
            accept={ACCEPTED_TYPES}
            onChange={handleFileChange}
            className="hidden"
          />
        </Card>
      )}

      {state === "extracting" && (
        <Card className="p-6">
          <div className="flex items-center gap-3" aria-live="polite">
            <Loader2 className="h-5 w-5 animate-spin text-secondary" />
            <div>
              <p className="text-sm font-medium">Extracting text from {fileName}...</p>
              <p className="text-xs text-muted-foreground">This may take a moment for scanned documents.</p>
            </div>
          </div>
        </Card>
      )}

      {state === "success" && (
        <Card className="p-6">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="h-5 w-5 text-success shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium flex items-center gap-2">
                  <FileText className="h-4 w-4" /> {fileName || "Resume"}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {result?.wordCount ?? 0} words extracted
                  {result?.method && ` via ${result.method}`}
                </p>
              </div>
            </div>
            <Button variant="ghost" size="icon" onClick={handleClear} className="h-8 w-8 shrink-0">
              <X className="h-4 w-4" />
              <span className="sr-only">Remove resume</span>
            </Button>
          </div>
        </Card>
      )}

      {state === "error" && (
        <Card className="p-6 border-destructive/30">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-destructive">{errorMsg}</p>
                <Button variant="outline" size="sm" className="mt-2" onClick={handleClear}>
                  Try again
                </Button>
              </div>
            </div>
          </div>
        </Card>
      )}

      <p className="text-sm text-muted-foreground">
        Don&apos;t have a resume? No problem &mdash; we&apos;ll match based on your work history.
      </p>
    </div>
  );
}
