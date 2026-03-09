"use client";

import { useState, useRef, useCallback } from "react";
import { FileText, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getCareerCenterPackage } from "@/lib/api";
import { CareerCenterPrintLayout } from "./CareerCenterPackage";
import type { CareerCenterPackage } from "@/lib/types";

interface CareerCenterExportProps {
  sessionId: string;
  token?: string;
}

export function CareerCenterExport({ sessionId, token }: CareerCenterExportProps) {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [packageData, setPackageData] = useState<CareerCenterPackage | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  const handleDownload = useCallback(async () => {
    setGenerating(true);
    setError(null);
    try {
      const data = await getCareerCenterPackage(sessionId, token);
      const { flushSync } = await import("react-dom");
      flushSync(() => setPackageData(data));
      if (!contentRef.current) {
        throw new Error("Print layout failed to render");
      }
      const html2pdf = (await import("html2pdf.js")).default;
      const date = new Date().toISOString().split("T")[0];
      await html2pdf()
        .set({
          margin: [10, 10, 10, 10],
          filename: `montgowork-career-center-${date}.pdf`,
          image: { type: "jpeg", quality: 0.98 },
          html2canvas: { scale: 2, useCORS: true },
          jsPDF: { unit: "mm", format: "letter", orientation: "portrait" },
          pagebreak: { mode: ["avoid-all", "css", "legacy"] },
        })
        .from(contentRef.current)
        .save();
    } catch {
      setError("Failed to generate PDF. Please try again.");
    } finally {
      setGenerating(false);
    }
  }, [sessionId, token]);

  return (
    <>
      <div className="flex flex-col items-center gap-1.5">
        <Button
          size="sm"
          onClick={handleDownload}
          disabled={generating}
          className="gap-1.5 text-xs bg-secondary text-secondary-foreground hover:bg-secondary/90"
          aria-label={generating ? "Generating PDF, please wait" : "Career Center PDF"}
        >
          {generating ? (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <FileText className="h-3.5 w-3.5" />
              Download PDF
            </>
          )}
        </Button>
        {error && <p role="alert" className="text-xs text-destructive">{error}</p>}
      </div>

      {packageData && (
        <div
          aria-hidden="true"
          style={{ position: "absolute", left: "-9999px", top: 0, width: "210mm" }}
        >
          <CareerCenterPrintLayout ref={contentRef} data={packageData} />
        </div>
      )}
    </>
  );
}
