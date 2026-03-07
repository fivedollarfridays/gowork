"use client";

import { useState, useRef, useCallback } from "react";
import { FileText, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getCareerCenterPackage } from "@/lib/api";
import { CareerCenterPrintLayout } from "./CareerCenterPackage";
import type { CareerCenterPackage } from "@/lib/types";

interface CareerCenterExportProps {
  sessionId: string;
}

export function CareerCenterExport({ sessionId }: CareerCenterExportProps) {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [packageData, setPackageData] = useState<CareerCenterPackage | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  const handleDownload = useCallback(async () => {
    setGenerating(true);
    setError(null);
    try {
      const data = await getCareerCenterPackage(sessionId);
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
  }, [sessionId]);

  return (
    <>
      <div className="flex items-center gap-2">
        <Button
          onClick={handleDownload}
          disabled={generating}
          className="gap-2"
          aria-label={generating ? "Generating PDF, please wait" : "Career Center PDF"}
        >
          {generating ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <FileText className="h-4 w-4" />
              Career Center PDF
            </>
          )}
        </Button>
        {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
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
