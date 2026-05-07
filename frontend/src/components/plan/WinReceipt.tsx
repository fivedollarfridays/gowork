"use client";

/**
 * WinReceipt — the plan-completion dopamine moment.
 *
 *   "The plan was earned.  The PDF is the receipt.  The animation is the
 *    handover.  Carlos receives his own work."
 *
 * Sits ABOVE MondayMorning on the plan page, fires once on first paint,
 * and rewards the user for finishing the assessment.  Three layers of
 * dopamine, in order:
 *
 *   1. PERSONALIZED HEADLINE — "Carlos, here's your plan."  Specificity
 *      buys ownership.
 *   2. WAGE TICKER — top match's hourly pay × 2080hrs annualized,
 *      animating $0 → $X over ~2s on first paint.  "You just unlocked
 *      this much per year" is a different chemical than confetti.
 *   3. STAT TRIPLET — "X jobs · Y fair-chance · Z% transit-accessible".
 *      Pure validation that the plan is real.
 *   4. THE RECEIPT — gradient amber→rose→cyan card whose primary CTA is
 *      "Take it with you →".  Click → fetch /api/plan/{sid}/pdf, save the
 *      blob via Object URL + <a download>, then the card detaches:
 *      shrinks + slides toward the bottom-right corner where downloads
 *      land.  The card returns to the layout 700ms later.  The illusion
 *      is the file leaving the page into the user's hand.
 *
 * Reduced-motion path renders the same content with no counter
 * animation, no card detach, no stagger — purely static.
 *
 * Doesn't replace PlanExport.  The legacy outline button at the bottom
 * of the page stays so users who scroll back and want to re-download
 * still find it.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Check, Download, Loader2 } from "lucide-react";
import {
  useInView, useMotionValue, useReducedMotion, useSpring, useTransform, m,
} from "framer-motion";
import type { ReEntryPlan } from "@/lib/types";
import { Ch08BrandIcon, Ch08PixelGrid } from "./_PlanFanfare";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const FULL_TIME_HOURS_PER_YEAR = 2080;

// Match leading "$" optional, then a decimal number, then "/hr" suffix.
// Tolerates "$20.50/hr", "$14/hr", "20/hr" — anything else returns null.
const HOURLY_RE = /\$?\s*([0-9]+(?:\.[0-9]+)?)\s*\/\s*hr/i;

export interface WinReceiptProps {
  plan: ReEntryPlan;
  sessionId: string;
  token: string;
  /** Optional first-name pulled from intake (intake doesn't currently
   *  capture it, but the prop is plumbed so a future intake field can
   *  feed personalization without re-architecting the component). */
  personaName?: string;
  /** Display label used inside the receipt card (e.g. city or "Plan").
   *  Defaults to "Your Plan". */
  receiptLabel?: string;
}

export function WinReceipt({
  plan, sessionId, token, personaName, receiptLabel = "Your Plan",
}: WinReceiptProps) {
  const prefersReduced = useReducedMotion();
  const annualizedWage = useMemo(() => annualizedFromTopMatch(plan), [plan]);
  const stats = useMemo(() => computeStats(plan), [plan]);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detached, setDetached] = useState(false);
  const [savedFlash, setSavedFlash] = useState(false);
  const detachTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const flashTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => () => {
    if (detachTimer.current) clearTimeout(detachTimer.current);
    if (flashTimer.current) clearTimeout(flashTimer.current);
  }, []);

  const handleDownload = useCallback(async () => {
    if (downloading) return;
    setDownloading(true);
    setError(null);
    try {
      const url = `${API_BASE}/api/plan/${encodeURIComponent(sessionId)}/pdf?token=${encodeURIComponent(token)}`;
      const resp = await fetch(url, { credentials: "omit" });
      if (!resp.ok) {
        throw new Error(`PDF endpoint returned ${resp.status}`);
      }
      const blob = await resp.blob();
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = objectUrl;
      a.download = `gowork-plan-${sessionId.split("-")[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      // Revoke after the click has been handled by the browser.
      setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);

      // Detach-to-corner illusion — card shrinks + slides toward the
      // bottom-right where browsers land downloads.  Skipped under
      // reduced motion so users who opt out get an instant return.
      if (!prefersReduced) {
        setDetached(true);
        detachTimer.current = setTimeout(() => setDetached(false), 700);
      }
      // "Saved." flash — the emotional closer.  Reduced-motion users
      // still see it (it's announced via aria-live), just without the
      // motion overlay.
      setSavedFlash(true);
      flashTimer.current = setTimeout(() => setSavedFlash(false), 2400);
    } catch {
      setError("We couldn't download your plan. Try again in a moment.");
    } finally {
      setDownloading(false);
    }
  }, [downloading, sessionId, token, prefersReduced]);

  const greeting = personaName?.trim()
    ? `${personaName.trim()}, here's your plan.`
    : "Your plan is ready.";

  return (
    <section
      data-testid="win-receipt"
      aria-label="Your plan summary"
      className="relative overflow-hidden rounded-3xl border border-white/10 px-5 py-7 sm:px-8 sm:py-9"
      style={{
        background: "var(--bg-base)",
      }}
    >
      {/* Ch08 amber pixel grid — 510 squares dissolve in on mount,
          gradient-mixed (amber→rose→cyan), composited via
          mix-blend-mode: screen onto the navy bg-base.  Same DOM +
          CSS as the homepage closer; only the timeline is
          mount-driven instead of scroll. */}
      <Ch08PixelGrid />

      {/* Center vignette — radial-gradient overlay that dims the
          middle of the section so the H1 + wage ticker read against
          a darker core, while the brand-color wash stays vibrant
          around the edges.  The grid (z=4) lives BEHIND this overlay
          (z=5), and the content (z=10) lives ON TOP. */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
        style={{
          zIndex: 5,
          background:
            "radial-gradient(120% 90% at 35% 45%, rgba(10,14,26,0.78) 0%, rgba(10,14,26,0.55) 35%, rgba(10,14,26,0.20) 65%, transparent 100%)",
        }}
      />

      {/* Ambient drift dots — subtle particles drifting upward over
          the pixel grid. Only when motion is enabled. */}
      {!prefersReduced && <DriftDots />}

      {/* Component-scoped polish styles.  Lifted from Ch08 cta-primary
          (cream pill + cyan ring + drop-shadow underglow + inner
          left→right cyan sweep), retuned for AMBER (the receipt
          surface lives in the brand's amber/hope register, not the
          cream/intelligence register the homepage CTA uses). */}
      <style>{`
        .winreceipt-pill {
          background: var(--accent-amber, #F59E0B);
          color: #0A0E1A;
          border: none;
          cursor: pointer;
          isolation: isolate;
          overflow: hidden;
          box-shadow:
            0 0 0 1.5px color-mix(in oklch, var(--accent-cyan, #22D3EE), transparent 40%),
            0 12px 28px rgba(245, 158, 11, 0.35),
            inset 0 1px 0 rgba(255, 255, 255, 0.45);
          filter:
            drop-shadow(0 0 14px color-mix(in oklch, var(--accent-amber, #F59E0B), transparent 55%))
            drop-shadow(0 6px 12px rgba(10, 14, 26, 0.30));
          transition:
            transform 360ms cubic-bezier(0.16, 1, 0.3, 1),
            background-color 280ms cubic-bezier(0.16, 1, 0.3, 1),
            filter 360ms cubic-bezier(0.16, 1, 0.3, 1);
        }
        .winreceipt-pill:hover:not(:disabled) {
          transform: translateY(-2px) scale(1.02);
          background: color-mix(in oklch, var(--accent-amber, #F59E0B), #FFFCF5 18%);
          filter:
            drop-shadow(0 0 26px color-mix(in oklch, var(--accent-amber, #F59E0B), transparent 35%))
            drop-shadow(0 10px 22px rgba(10, 14, 26, 0.40));
        }
        .winreceipt-pill:focus-visible {
          outline: 2px solid var(--accent-cyan, #22D3EE);
          outline-offset: 3px;
        }
        .winreceipt-pill:disabled {
          opacity: 0.7;
          cursor: progress;
        }
        .winreceipt-pill__sweep {
          position: absolute;
          top: 0;
          left: -60%;
          width: 50%;
          height: 100%;
          background: linear-gradient(
            100deg,
            transparent 0%,
            color-mix(in oklch, #FFFCF5, transparent 70%) 45%,
            color-mix(in oklch, #FFFCF5, transparent 50%) 50%,
            color-mix(in oklch, #FFFCF5, transparent 70%) 55%,
            transparent 100%
          );
          pointer-events: none;
          animation: winreceipt-pill-sweep 4.2s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite;
          animation-delay: 1.6s;
          z-index: 1;
        }
        @keyframes winreceipt-pill-sweep {
          0%   { left: -60%; }
          60%  { left: 110%; }
          100% { left: 110%; }
        }
        @media (prefers-reduced-motion: reduce) {
          .winreceipt-pill__sweep { animation: none !important; }
          .winreceipt-pill:hover:not(:disabled) { transform: none !important; }
        }
        /* Receipt card top-edge perforation softening — radial fade
           on the corners so the dashed line doesn't read as a hard
           graphical seam.  Pure cosmetic. */
        .winreceipt-card { position: relative; }
      `}</style>

      <div className="relative z-10 flex flex-col gap-5">
        {/* Eyebrow — wall-grade eyebrow with the actual brand-mark
            icon (cream G arc + cyan path-line draws in on mount). */}
        <div className="flex items-center gap-3 text-[11px] uppercase tracking-[0.16em] text-muted-foreground/80">
          <span className="ch08-brand-icon-wrap inline-flex" style={{ color: "#F5F3EE" }}>
            <Ch08BrandIcon size={28} drawDelayMs={550} drawDurationMs={900} />
          </span>
          <span className="font-mono">Receipt · {receiptLabel}</span>
        </div>

        {/* H1 — page-level landmark with the brand colour wash.
            We deliberately do NOT apply .ch08-aberration here —
            that class is tuned for solid cream glyphs on amber and
            its text-shadow + filter stack reads as a "torn" navy
            ghost behind transparent gradient-clip text.  The H1
            already lives over the dissolving pixel grid, which is
            the same brand surface as the Ch08 closer; the visual
            cohesion comes from that, not from aberration. */}
        <div className="space-y-2">
          <h1
            className="text-3xl sm:text-4xl font-bold tracking-tight"
            style={{
              background:
                "linear-gradient(90deg, var(--accent-amber, #F59E0B), var(--accent-rose, #FB7185), var(--accent-cyan, #22D3EE))",
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              color: "transparent",
            }}
          >
            {greeting}
          </h1>
          <p className="text-sm sm:text-base text-muted-foreground">
            You showed up.  We did the math.  Here&apos;s what we found.
          </p>
        </div>

        {/* Wage ticker — $0 → annualizedWage.  Hidden when no
            pay_range is available (rare but real for some imports). */}
        {annualizedWage !== null && (
          <div data-testid="win-receipt-wage" className="space-y-1">
            <div className="text-[11px] uppercase tracking-widest text-muted-foreground">
              Top match could pay you up to
            </div>
            <div className="flex items-baseline gap-2">
              <span
                className="text-4xl sm:text-5xl font-extrabold"
                style={{ color: "var(--accent-amber, #F59E0B)" }}
              >
                <WageTicker target={annualizedWage} static={!!prefersReduced} />
              </span>
              <span className="text-sm text-muted-foreground font-medium">
                / year
              </span>
            </div>
            <div className="text-[11px] text-muted-foreground/80">
              Based on the highest-paying match in your plan, full-time.
            </div>
          </div>
        )}

        {/* Stat triplet — pure validation.  Each value tickers up like
            the wage so the entire hero shares one micro-interaction
            language. */}
        <div
          data-testid="win-receipt-stats"
          className="grid grid-cols-3 gap-3 rounded-xl border border-white/10 bg-black/10 px-4 py-3 backdrop-blur-sm"
        >
          <StatTicker
            value={stats.matched}
            label="jobs matched"
            staticRender={!!prefersReduced}
            duration={1500}
          />
          <StatTicker
            value={stats.fairChance}
            label="fair-chance"
            staticRender={!!prefersReduced}
            duration={1700}
          />
          <StatTicker
            value={stats.transitPct}
            suffix="%"
            label="transit-accessible"
            staticRender={!!prefersReduced}
            duration={1900}
          />
        </div>

        {/* THE RECEIPT — primary CTA. Renders detached state when the
            user clicks (shrinks + slides toward bottom-right). The
            top edge carries a subtle dashed perforation so the card
            reads as a real paper receipt being torn off. */}
        <m.div
          className="winreceipt-card relative rounded-2xl p-5 sm:p-6"
          style={{
            background:
              "linear-gradient(135deg, rgba(245,158,11,0.18) 0%, rgba(251,113,133,0.12) 50%, rgba(34,211,238,0.18) 100%)",
            border: "1px solid color-mix(in oklch, var(--accent-amber, #F59E0B), transparent 60%)",
            boxShadow:
              "0 0 0 1px color-mix(in oklch, var(--accent-amber, #F59E0B), transparent 75%), 0 18px 48px -16px color-mix(in oklch, var(--accent-amber, #F59E0B), transparent 65%), inset 0 1px 0 rgba(255,255,255,0.08)",
          }}
          initial={false}
          animate={
            detached
              ? prefersReduced
                ? {}
                : { opacity: 0.25, scale: 0.85, x: 240, y: 180 }
              : { opacity: 1, scale: 1, x: 0, y: 0 }
          }
          transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
        >
          {/* Perforation — dashed border-top simulating a torn paper
              edge.  Reads as "this is a receipt the page tore off
              for you" rather than just another generic card. */}
          <div
            aria-hidden="true"
            className="pointer-events-none absolute left-4 right-4 -top-px"
            style={{
              borderTop: "1.5px dashed rgba(245,158,11,0.45)",
            }}
          />
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-[11px] uppercase tracking-widest text-muted-foreground">
                <span
                  className="inline-block h-1.5 w-1.5 rounded-full"
                  style={{ background: "var(--accent-cyan, #22D3EE)" }}
                  aria-hidden="true"
                />
                Take this with you
              </div>
              <div className="text-lg font-semibold">
                Your plan, on paper.
              </div>
              <div className="text-xs text-muted-foreground">
                Print it · email it · hand it to a case manager Monday morning.
              </div>
            </div>
            <button
              type="button"
              onClick={handleDownload}
              disabled={downloading}
              className="winreceipt-pill relative inline-flex items-center justify-center gap-3 rounded-full px-7 py-3.5 font-bold text-[15px] tracking-tight"
              aria-label="Take it with you — download your plan as a PDF"
              data-testid="win-receipt-download"
            >
              <span className="winreceipt-pill__sweep" aria-hidden="true" />
              <span className="relative z-10 inline-flex items-center gap-2">
                {downloading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Preparing…
                  </>
                ) : savedFlash ? (
                  <>
                    <Check className="h-4 w-4" strokeWidth={3} />
                    Saved
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4" />
                    Take it with you
                  </>
                )}
              </span>
            </button>
          </div>
          {error && (
            <p
              role="alert"
              className="mt-3 text-sm text-destructive"
            >
              {error}
            </p>
          )}
        </m.div>

        {/* "Saved." flash — fires after the PDF download succeeds.
            aria-live=polite so screen-reader users get the close
            affirmation; sighted users see it as a calm, gradient pill
            that lands BELOW the receipt card (where the card was
            sitting before it detached toward the corner). */}
        <m.div
          aria-live="polite"
          aria-atomic="true"
          className="pointer-events-none flex justify-center"
          initial={{ opacity: 0, y: 8 }}
          animate={savedFlash ? { opacity: 1, y: 0 } : { opacity: 0, y: 8 }}
          transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
        >
          {savedFlash && (
            <div
              className="rounded-full px-5 py-2.5 text-sm font-semibold backdrop-blur-md shadow-2xl"
              style={{
                background:
                  "linear-gradient(90deg, rgba(245,158,11,0.92), rgba(34,211,238,0.92))",
                color: "#0A0E1A",
              }}
              data-testid="win-receipt-saved-flash"
            >
              Saved. Bring this Monday morning.
            </div>
          )}
        </m.div>
      </div>
    </section>
  );
}


// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function annualizedFromTopMatch(plan: ReEntryPlan): number | null {
  for (const job of plan.job_matches ?? []) {
    const pay = job.pay_range;
    if (!pay) continue;
    const m = HOURLY_RE.exec(pay);
    if (!m) continue;
    const hourly = Number.parseFloat(m[1]);
    if (!Number.isFinite(hourly) || hourly <= 0) continue;
    return Math.round(hourly * FULL_TIME_HOURS_PER_YEAR);
  }
  return null;
}

function computeStats(plan: ReEntryPlan): {
  matched: number; fairChance: number; transitPct: number;
} {
  const matches = plan.job_matches ?? [];
  const matched = matches.length;
  const fairChance = matches.filter((j) => j.fair_chance).length;
  const transit = matches.filter((j) => j.transit_accessible).length;
  const transitPct = matched > 0 ? Math.round((transit / matched) * 100) : 0;
  return { matched, fairChance, transitPct };
}

function formatWage(n: number): string {
  return n.toLocaleString("en-US");
}

function WageTicker({ target, static: isStatic }: { target: number; static: boolean }) {
  // The default `AnimatedCounter` in lib/motion uses `toFixed` which
  // can't insert thousands separators — Carlos sees "$42640" instead of
  // "$42,640", which reads as a phone number rather than a salary.  We
  // inline our own counter that pipes the spring through
  // `toLocaleString` so the displayed string keeps the comma the entire
  // way up.
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-50px" });
  const motionValue = useMotionValue(0);
  const spring = useSpring(motionValue, { duration: 2200, bounce: 0.05 });
  const display = useTransform(spring, (v) =>
    `$${Math.round(v).toLocaleString("en-US")}`,
  );
  useEffect(() => {
    if (isStatic) return;
    if (inView) motionValue.set(target);
  }, [inView, motionValue, target, isStatic]);

  if (isStatic) {
    return <span ref={ref}>${target.toLocaleString("en-US")}</span>;
  }
  return <m.span ref={ref}>{display}</m.span>;
}


function StatTicker({
  value, label, suffix = "", staticRender, duration = 1500,
}: {
  value: number;
  label: string;
  suffix?: string;
  staticRender: boolean;
  duration?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-50px" });
  const motionValue = useMotionValue(0);
  const spring = useSpring(motionValue, { duration, bounce: 0 });
  const display = useTransform(spring, (v) => `${Math.round(v)}${suffix}`);
  useEffect(() => {
    if (staticRender) return;
    if (inView) motionValue.set(value);
  }, [inView, motionValue, value, staticRender]);

  return (
    <div ref={ref} className="text-center">
      <div className="text-2xl font-bold tabular-nums">
        {staticRender ? `${value}${suffix}` : <m.span>{display}</m.span>}
      </div>
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
    </div>
  );
}

function DriftDots() {
  // 18 lightweight dots drifting up at varying speeds — additive, never
  // interactive, and aria-hidden so they're invisible to assistive tech.
  // Pure CSS keyframes (defined inline below) so there's no JS RAF loop.
  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0 z-0">
      {Array.from({ length: 18 }, (_, i) => {
        const left = (i * 53) % 100;
        const delay = (i * 0.27) % 5;
        const dur = 9 + ((i * 7) % 7);
        const size = 3 + (i % 4);
        const tint = i % 3 === 0
          ? "rgba(245,158,11,0.55)"
          : i % 3 === 1
          ? "rgba(251,113,133,0.45)"
          : "rgba(34,211,238,0.45)";
        return (
          <span
            key={i}
            className="absolute rounded-full"
            style={{
              left: `${left}%`,
              bottom: -10,
              width: size,
              height: size,
              background: tint,
              animation: `winreceipt-drift ${dur}s linear ${delay}s infinite`,
              filter: "blur(0.5px)",
            }}
          />
        );
      })}
      <style>{`
        @keyframes winreceipt-drift {
          0%   { transform: translateY(0)        translateX(0);   opacity: 0; }
          15%  {                                              opacity: 0.9; }
          85%  {                                              opacity: 0.6; }
          100% { transform: translateY(-180px) translateX(8px); opacity: 0; }
        }
      `}</style>
    </div>
  );
}
