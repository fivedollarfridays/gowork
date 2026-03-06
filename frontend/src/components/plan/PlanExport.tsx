"use client";

import { useState, useRef, useCallback } from "react";
import { Download, Loader2 } from "lucide-react";
import { QRCodeSVG } from "qrcode.react";
import { Button } from "@/components/ui/button";
import type { ReEntryPlan, CreditAssessmentResult } from "@/lib/types";
import { PDF_SEVERITY_COLORS } from "@/lib/constants";

interface PlanExportProps {
  plan: ReEntryPlan;
  creditResult?: CreditAssessmentResult | null;
  feedbackToken?: string | null;
}

export function PlanExport({ plan, creditResult, feedbackToken }: PlanExportProps) {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  const handleDownload = useCallback(async () => {
    if (!contentRef.current) return;
    setGenerating(true);
    setError(null);
    try {
      const html2pdf = (await import("html2pdf.js")).default;
      await html2pdf()
        .set({
          margin: [10, 10, 10, 10],
          filename: `montgowork-plan-${plan.session_id}.pdf`,
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
  }, [plan.session_id]);

  const today = new Date().toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <>
      <div className="flex items-center gap-2">
        <Button
          onClick={handleDownload}
          disabled={generating}
          variant="outline"
          className="gap-2"
          aria-label={generating ? "Generating PDF, please wait" : undefined}
        >
          {generating ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Download className="h-4 w-4" />
              Download PDF
            </>
          )}
        </Button>
        {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
      </div>

      {/* Hidden print-ready content — always mounted for html2pdf ref access */}
      <div
        ref={contentRef}
        aria-hidden="true"
        style={{
          position: "absolute",
          left: "-9999px",
          top: 0,
          width: "210mm",
          fontFamily: "Arial, Helvetica, sans-serif",
          fontSize: "12px",
          lineHeight: "1.5",
          color: "#1a1a1a",
          background: "#ffffff",
          padding: "16px",
        }}
      >
        <PdfHeader date={today} />
        <PdfSummary summary={plan.resident_summary} />
        <PdfBarriers barriers={plan.barriers} />
        <PdfJobMatches jobs={plan.job_matches} />
        <PdfNextSteps steps={plan.immediate_next_steps} />
        {creditResult && <PdfCreditInfo creditResult={creditResult} />}
        {feedbackToken && <PdfFeedbackQR token={feedbackToken} />}
      </div>
    </>
  );
}

const sectionHeading = { fontSize: "16px", fontWeight: "bold", marginBottom: "8px" } as const;
const sectionSpacing = { marginBottom: "16px" } as const;

function PdfHeader({ date }: { date: string }) {
  return (
    <div style={{ borderBottom: "2px solid #0d9488", paddingBottom: "8px", ...sectionSpacing }}>
      <h1 style={{ fontSize: "22px", fontWeight: "bold", color: "#0d9488", margin: 0 }}>
        MontGoWork Re-Entry Plan
      </h1>
      <p style={{ fontSize: "11px", color: "#6b7280", margin: "4px 0 0" }}>
        Generated {date}
      </p>
    </div>
  );
}

function PdfSummary({ summary }: { summary: string | null }) {
  if (!summary) return null;
  return (
    <div
      style={{
        background: "#f0fdfa",
        border: "1px solid #ccfbf1",
        borderRadius: "6px",
        padding: "12px",
        ...sectionSpacing,
      }}
    >
      <p style={{ fontStyle: "italic", margin: 0 }}>{summary}</p>
    </div>
  );
}

function PdfBarriers({ barriers }: { barriers: ReEntryPlan["barriers"] }) {
  if (barriers.length === 0) return null;
  return (
    <div style={sectionSpacing}>
      <h2 style={sectionHeading}>Barriers</h2>
      {barriers.map((b) => {
        const colors = PDF_SEVERITY_COLORS[b.severity] ?? PDF_SEVERITY_COLORS.low;
        return (
          <div
            key={b.type}
            style={{
              border: "1px solid #e5e7eb",
              borderRadius: "6px",
              padding: "10px",
              marginBottom: "8px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
              <strong>{b.title}</strong>
              <span
                style={{
                  fontSize: "10px",
                  padding: "2px 6px",
                  borderRadius: "4px",
                  background: colors.bg,
                  color: colors.text,
                }}
              >
                {b.severity}
              </span>
            </div>
            {b.actions.length > 0 && (
              <ol style={{ margin: "4px 0 0", paddingLeft: "18px", fontSize: "11px" }}>
                {b.actions.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ol>
            )}
          </div>
        );
      })}
    </div>
  );
}

function PdfJobMatches({ jobs }: { jobs: ReEntryPlan["job_matches"] }) {
  if (jobs.length === 0) return null;
  return (
    <div style={sectionSpacing}>
      <h2 style={sectionHeading}>Job Matches</h2>
      {jobs.map((job, i) => (
        <div
          key={`${job.title}-${i}`}
          style={{ border: "1px solid #e5e7eb", borderRadius: "6px", padding: "10px", marginBottom: "8px" }}
        >
          <strong>{job.title}</strong>
          {job.company && <span style={{ color: "#6b7280" }}> at {job.company}</span>}
          <div style={{ fontSize: "11px", marginTop: "4px" }}>
            {job.eligible_now ? (
              <span style={{ color: PDF_SEVERITY_COLORS.low.text }}>Eligible Now</span>
            ) : (
              <span style={{ color: PDF_SEVERITY_COLORS.medium.text }}>
                {job.eligible_after ?? "After barrier resolution"}
              </span>
            )}
            {job.location && (
              <span style={{ marginLeft: "12px", color: "#6b7280" }}>{job.location}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function PdfNextSteps({ steps }: { steps: string[] }) {
  if (steps.length === 0) return null;
  return (
    <div style={sectionSpacing}>
      <h2 style={sectionHeading}>Immediate Next Steps</h2>
      <ol style={{ margin: 0, paddingLeft: "18px", fontSize: "12px" }}>
        {steps.map((step, i) => (
          <li key={i} style={{ marginBottom: "4px" }}>{step}</li>
        ))}
      </ol>
    </div>
  );
}

function PdfCreditInfo({ creditResult }: { creditResult: CreditAssessmentResult }) {
  return (
    <div style={sectionSpacing}>
      <h2 style={sectionHeading}>Credit Assessment</h2>
      <div style={{ border: "1px solid #e5e7eb", borderRadius: "6px", padding: "10px" }}>
        <p style={{ margin: "0 0 4px" }}>
          <strong>FICO Score:</strong> {creditResult.readiness.fico_score} ({creditResult.readiness.score_band})
        </p>
        <p style={{ margin: "0 0 4px" }}>
          <strong>Readiness Score:</strong> {creditResult.readiness.score}/100
        </p>
        {creditResult.dispute_pathway.total_estimated_days > 0 && (
          <p style={{ margin: 0, fontSize: "11px", color: "#6b7280" }}>
            Estimated repair timeline: {creditResult.dispute_pathway.total_estimated_days} days
          </p>
        )}
      </div>
    </div>
  );
}

function PdfFeedbackQR({ token }: { token: string }) {
  const url = `${window.location.origin}/feedback/${token}`;
  return (
    <div
      style={{
        borderTop: "1px solid #e5e7eb",
        paddingTop: "16px",
        marginTop: "16px",
        textAlign: "center",
      }}
    >
      <p style={{ fontSize: "13px", fontWeight: "bold", margin: "0 0 8px" }}>
        How did your visit go? Help us improve for the next person.
      </p>
      <QRCodeSVG data-testid="feedback-qr" value={url} size={100} level="M" />
      <p style={{ fontSize: "10px", color: "#6b7280", margin: "6px 0 0" }}>
        Scan to share feedback
      </p>
    </div>
  );
}
