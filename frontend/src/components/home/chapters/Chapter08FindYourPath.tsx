"use client";

/**
 * Chapter 08 — Find Your Path. The site's MIC-DROP. Pin + scrub
 * timeline that locks the section in brand amber, then drops the
 * Go Work brand mark on top in horizontal composition: brand
 * cluster (icon + Go/Work stack) on the LEFT, "Get your plan" CTA
 * on the RIGHT — matching the brand-mark spec scaled up to hero.
 *
 *   stage 0 (t=0)        eyebrow lands
 *   stage 1–4 (0.4→3.4)  manifesto lines slide in alternating L/R
 *   stage 5 (3.4→4.0)    DWELL — manifesto fully visible
 *   stage 6 (4.0→7.0)    PIXELIZE (slow, 3.0s) — 510 amber squares
 *                        (#F59E0B) fade in (bottom-biased + sine +
 *                        random) so the wave reads.
 *   stage 7 (6.6→7.2)    MANIFESTO EXITS, fast and tight. Amber
 *                        grid STAYS — the section is now a locked
 *                        amber field.
 *   stage 8 (7.0→8.4)    BRAND ICON SLIDES IN FROM RIGHT
 *                        (clamp(180px, 22vw, 380px)). Cream G arc
 *                        + cyan path-line (line still hidden).
 *   stage 9 (8.0→9.0)    CYAN PATH-LINE DRAWS through the icon
 *                        (stroke-dashoffset 192 → 0).
 *   stage 10 (8.6→9.8)   "Go" SLIDES IN FROM RIGHT — solid cream
 *                        on amber, single subtle cyan aberration
 *                        offset on the leading edge (3px settled,
 *                        ramp from 12px), multi-layer navy drop-
 *                        shadow stack for extruded depth.
 *   stage 11 (9.4→10.6)  "Work" SLIDES IN FROM RIGHT, italic axis.
 *   stage 12 (10.6→11.4) CHROMATIC GLITCH PULSE — aberration
 *                        spikes to 14px then snaps to 2px resting.
 *   stage 13 (11.4→12.4) CTA SLIDES IN FROM RIGHT EDGE of section,
 *                        completing the [BRAND] —— [ACTION] visual
 *                        handoff.
 *   stage 14 (12.4→13.2) LIFT — composition floats up (yPercent → -6).
 *   stage 15 (13.2→14.0) SETTLE — drops back (yPercent -6 → 0).
 *
 * Pin range: +=460%. Scrub: 0.6 (reverses cleanly on scroll-up).
 * Z-stacking: manifesto (3) → amber pixel grid (4) → mic-drop (5).
 * Reduced-motion: pixel grid hidden via CSS, aberration disabled,
 * manifesto + mic-drop + CTA static at first paint.
 *
 * View Transitions API still wraps the CTA navigation when supported.
 */

import { useEffect, useRef, useState, type MouseEvent } from "react";
import { useRouter } from "next/navigation";
import { useTranslation } from "@/hooks/useTranslation";
import { usePrefersReducedMotion } from "@/hooks/usePrefersReducedMotion";
import { useViewTransitionsSupport } from "@/hooks/useViewTransitionsSupport";

export interface Chapter08FindYourPathProps {
  id?: string;
}

const SPOKEN_CITIES = ["Montgomery, AL", "Dallas, TX", "Houston, TX"] as const;

// Pixel-digitize grid dimensions — 30 cols × 17 rows = 510 squares.
// Matches Lithosquare's reference geometry exactly.
const PIXEL_COLS = 30;
const PIXEL_ROWS = 17;

// Brand gradient stops (hex) for the per-square colour mixing on
// the amber pixel grid. The pixel field reads as a continuous
// brand gradient (amber → rose → cyan) when fully filled, matching
// the colour wash used elsewhere in the site (Carlos h2, hero
// morph word, etc.) so Ch08 closes with a colour family that's
// continuous with the homepage.
const STOP_AMBER: [number, number, number] = [0xF5, 0x9E, 0x0B]; // #F59E0B
const STOP_ROSE:  [number, number, number] = [0xFB, 0x71, 0x85]; // #FB7185
const STOP_CYAN:  [number, number, number] = [0x22, 0xD3, 0xEE]; // #22D3EE

function lerp(a: number, b: number, t: number): number {
  return Math.round(a + (b - a) * t);
}
function mixGradientStop(t: number): string {
  // t ∈ [0, 1]. Two-segment lerp: amber→rose for t<0.5, rose→cyan
  // for t≥0.5. Returns an `rgb(r, g, b)` string for `style.background`.
  if (t <= 0.5) {
    const k = t / 0.5;
    return `rgb(${lerp(STOP_AMBER[0], STOP_ROSE[0], k)},${lerp(STOP_AMBER[1], STOP_ROSE[1], k)},${lerp(STOP_AMBER[2], STOP_ROSE[2], k)})`;
  }
  const k = (t - 0.5) / 0.5;
  return `rgb(${lerp(STOP_ROSE[0], STOP_CYAN[0], k)},${lerp(STOP_ROSE[1], STOP_CYAN[1], k)},${lerp(STOP_ROSE[2], STOP_CYAN[2], k)})`;
}

export function Chapter08FindYourPath({
  id = "chapter-08",
}: Chapter08FindYourPathProps) {
  const { t } = useTranslation();
  const reduced = usePrefersReducedMotion();
  const router = useRouter();
  const vtSupported = useViewTransitionsSupport();
  const sectionRef = useRef<HTMLElement | null>(null);
  const [hovered, setHovered] = useState(false);
  const [cityIdx, setCityIdx] = useState(0);

  // Build the pixel-digitize grid (30×17 = 510 squares) once on mount.
  // Sorted by priority: bottom rows first, with per-square randomness
  // and a sine-wave horizontal variation matching Lithosquare's
  // reference. The sorted order is what drives the dissolve cadence.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const el = sectionRef.current;
    if (!el) return;
    const grid = el.querySelector<HTMLDivElement>("[data-ch08-pixel-grid]");
    if (!grid) return;
    if (grid.childElementCount > 0) return; // already built (StrictMode)

    // Per-square colour mixing — when filled, the grid as a whole
    // reads as the brand homepage gradient (amber top-left → rose
    // mid → cyan bottom-right) instead of flat amber. Each square's
    // colour is computed from its (col, row) position so squares in
    // the top-left quadrant render amber, the diagonal middle
    // renders rose, and the bottom-right renders cyan. Same colour
    // family the hero + Carlos h2 use, so Ch08 closes with a colour
    // wash continuous with the rest of the site.
    const frag = document.createDocumentFragment();
    for (let row = 0; row < PIXEL_ROWS; row += 1) {
      for (let col = 0; col < PIXEL_COLS; col += 1) {
        const sq = document.createElement("div");
        sq.className = "ch08-square";
        sq.dataset.row = String(row);
        sq.dataset.col = String(col);
        // Diagonal gradient position: 0 (top-left) → 1 (bottom-right).
        const t = (col / (PIXEL_COLS - 1) + row / (PIXEL_ROWS - 1)) / 2;
        // Two-stop linear interpolation through brand accents:
        //   t=0.00..0.50  amber → rose
        //   t=0.50..1.00  rose  → cyan
        // Hex blending in sRGB — close enough for the dense pixel
        // grid where each square is small and the eye blends.
        sq.style.background = mixGradientStop(t);
        frag.appendChild(sq);
      }
    }
    grid.appendChild(frag);
  }, []);

  // Build the GSAP ScrollTrigger pin + scrub timeline.
  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    const el = sectionRef.current;
    if (!el) return undefined;
    if (reduced) {
      // Reduced-motion: paint final state — manifesto visible at top,
      // mic-drop composition (icon + GO + WORK + CTA) landed at rest,
      // cyan line drawn, no aberration. No pin, no scrub, no pixel
      // grid (CSS hides the grid in reduced-motion via media query).
      el.querySelectorAll<HTMLElement>("[data-ch08-line]").forEach((line) => {
        line.style.transform = "translate3d(0, 0, 0)";
        line.style.opacity = "1";
      });
      el.querySelectorAll<HTMLElement>("[data-ch08-row]").forEach((row) => {
        row.style.transform = "translateX(0)";
        row.style.opacity = "1";
        row.style.setProperty("--abr-x", "0px");
      });
      const wm = el.querySelector<HTMLElement>("[data-ch08-wordmark]");
      if (wm) wm.style.opacity = "1";
      const stageEl = el.querySelector<HTMLElement>("[data-ch08-stage]");
      if (stageEl) stageEl.style.opacity = "1";
      const icon = el.querySelector<HTMLElement>("[data-ch08-mic-icon]");
      if (icon) {
        icon.style.transform = "translateX(0)";
        icon.style.opacity = "1";
      }
      el.querySelectorAll<SVGElement>("[data-ch08-mic-line]").forEach(
        (line) => {
          (line as unknown as { style: CSSStyleDeclaration }).style.strokeDashoffset = "0";
        },
      );
      const ctaEl = el.querySelector<HTMLElement>("[data-ch08-cta]");
      if (ctaEl) {
        ctaEl.style.transform = "translateX(0)";
        ctaEl.style.opacity = "1";
      }
      const metaEl = el.querySelector<HTMLElement>("[data-ch08-meta]");
      if (metaEl) metaEl.style.opacity = "1";
      const lockupReducedEl = el.querySelector<HTMLElement>(
        "[data-ch08-mic-lockup]",
      );
      if (lockupReducedEl)
        lockupReducedEl.style.setProperty("--lockup-line-scale", "1");
      return undefined;
    }

    let stInst: { kill: () => void } | null = null;
    let cancelled = false;

    (async () => {
      try {
        const gsapMod = await import("gsap");
        const stMod = await import("gsap/ScrollTrigger");
        if (cancelled) return;
        const gsap = gsapMod.gsap;
        const ScrollTrigger = stMod.ScrollTrigger;
        gsap.registerPlugin(ScrollTrigger);

        const lines = gsap.utils.toArray<HTMLElement>("[data-ch08-line]", el);
        const eyebrow = el.querySelector("[data-ch08-eyebrow]");
        const cta = el.querySelector("[data-ch08-cta]");
        const meta = el.querySelector("[data-ch08-meta]");
        const wordmark = el.querySelector("[data-ch08-wordmark]");
        const stage = el.querySelector("[data-ch08-stage]");
        const pixelGrid = el.querySelector<HTMLElement>(
          "[data-ch08-pixel-grid]",
        );
        const micIcon = el.querySelector<HTMLElement>("[data-ch08-mic-icon]");
        // Three lines now (core + 2 glow halos). GSAP animates
        // strokeDashoffset on all of them in lockstep so the glow
        // draws WITH the core line.
        const micLines = Array.from(
          el.querySelectorAll<SVGElement>("[data-ch08-mic-line]"),
        );
        const goRow = el.querySelector<HTMLElement>('[data-ch08-row="row1"]');
        const workRow = el.querySelector<HTMLElement>('[data-ch08-row="row2"]');
        const lockupEl = el.querySelector<HTMLElement>(
          "[data-ch08-mic-lockup]",
        );

        // Pixel-digitize squares — sorted by priority. Lower priority
        // = appears first. Bottom rows weighted lower so the wavefront
        // flows bottom→top. Random factor dominates so the pattern
        // reads as organic pixel rain. Sine column variation adds a
        // subtle horizontal wave. Numbers match the Lithosquare ref.
        const squareEls = Array.from(
          el.querySelectorAll<HTMLElement>(".ch08-square"),
        );
        const sortedSquares = squareEls
          .map((square) => {
            const row = parseInt(square.dataset.row ?? "0", 10);
            const col = parseInt(square.dataset.col ?? "0", 10);
            const distanceFromBottom = PIXEL_ROWS - 1 - row;
            const basePriority = distanceFromBottom * 50;
            const randomFactor = Math.random() * 300;
            const waveEffect = Math.sin(col * 0.3) * 30;
            return {
              el: square,
              priority: basePriority + randomFactor + waveEffect,
            };
          })
          .sort((a, b) => a.priority - b.priority);

        // Initial state — manifesto stage on top + visible; manifesto
        // lines offstage; mic-drop children (icon + GO + WORK + CTA)
        // ALL offstage (icon/rows from RIGHT; CTA from BELOW) ready
        // for sequenced entry over the locked amber pixel field;
        // cyan path-line hidden (dashoffset 192); chromatic-aberration
        // offsets start large (12px) and settle to 2px during glitch;
        // pixel grid squares invisible (opacity 0); grid stays at
        // yPercent 0 throughout — it never slides off, so the amber
        // colour locks in once the squares are filled.
        if (eyebrow) gsap.set(eyebrow, { opacity: 0, x: -40 });
        lines.forEach((ln, i) => {
          gsap.set(ln, {
            xPercent: i % 2 === 0 ? -110 : 110,
            opacity: 0,
          });
        });
        if (cta) gsap.set(cta, { opacity: 0, xPercent: 60 });
        if (meta) gsap.set(meta, { opacity: 0 });
        if (wordmark) gsap.set(wordmark, { opacity: 1, yPercent: 0 });
        if (stage) gsap.set(stage, { yPercent: 0, opacity: 1 });
        if (pixelGrid) gsap.set(pixelGrid, { yPercent: 0, opacity: 1 });
        if (micIcon) gsap.set(micIcon, { xPercent: 140, opacity: 0 });
        if (micLines.length) {
          gsap.set(micLines, { strokeDashoffset: 192 });
        }
        if (goRow) gsap.set(goRow, { xPercent: 140, opacity: 0 });
        if (workRow) gsap.set(workRow, { xPercent: 140, opacity: 0 });
        // Aberration custom property — set via direct setProperty so
        // GSAP's CSS plugin doesn't have to wrestle with `--var-name`
        // syntax in vars objects (silent-fail risk in some build
        // chains). Driven by a proxy tween below.
        if (goRow) goRow.style.setProperty("--abr-x", "12px");
        if (workRow) workRow.style.setProperty("--abr-x", "12px");
        const abrProxy = { v: 12 };
        // Lockup cyan path-line — initial scaleX 0, GSAP scrubs to 1
        // after both Go + Work have landed. The lockup ref is
        // captured in a local non-null variable so the onUpdate
        // closure is TS-safe (was the silent-fail risk earlier).
        if (lockupEl) lockupEl.style.setProperty("--lockup-line-scale", "0");
        const lockupLineProxy = { v: 0 };
        sortedSquares.forEach((s) => {
          gsap.set(s.el, { opacity: 0 });
        });

        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: el,
            start: "top top",
            // 460% pin window — fits manifesto entry + dwell + slow
            // pixelize (3.0s) + manifesto exit + icon slide + cyan
            // path-line draw + GO/WORK + chromatic glitch + CTA
            // entry + lift/settle. GO WORK mic-drop on locked amber
            // with cyan CTA below is the closing image; no pixels
            // obscure it. Reverses cleanly on scroll-up.
            end: "+=460%",
            pin: true,
            scrub: 0.6,
            anticipatePin: 1,
          },
        });

        // STAGE 0 — eyebrow lands.
        if (eyebrow) {
          tl.to(eyebrow, { opacity: 1, x: 0, duration: 0.6, ease: "power3.out" }, 0);
        }

        // STAGE 1–4 — manifesto lines slide in alternating left/right.
        // No CTA at this stage anymore — the CTA enters AFTER the
        // GO WORK mic-drop has landed (see stage 13 below).
        lines.forEach((ln, i) => {
          const at = 0.4 + i * 0.7;
          tl.to(
            ln,
            { xPercent: 0, opacity: 1, duration: 0.9, ease: "power3.out" },
            at,
          );
        });

        // STAGE 5 — DWELL (3.4 → 4.0): manifesto fully visible.

        // STAGE 6 (4.0 → 7.0) — PIXELIZE. SLOWED to 3.0s (was 1.6s)
        // so the user can actually enjoy the wave. 510 amber squares
        // fade IN in priority order: bottom-biased + sine + random.
        // By the end, the manifesto is fully covered and the section
        // has become a locked amber field. Driven by a numeric proxy
        // tween + onUpdate that only mutates squares crossing the
        // visibility threshold this frame — keeps scroll-tied
        // playback smooth.
        const proxy = { v: 0 };
        let prevVisible = 0;
        const total = sortedSquares.length;
        tl.to(
          proxy,
          {
            v: 1,
            duration: 3.0,
            ease: "power1.inOut",
            onUpdate: () => {
              const visibleCount = Math.floor(total * proxy.v);
              if (visibleCount === prevVisible) return;
              if (visibleCount > prevVisible) {
                for (let i = prevVisible; i < visibleCount; i += 1) {
                  gsap.to(sortedSquares[i].el, {
                    opacity: 1,
                    duration: 0.6,
                    ease: "power2.out",
                    overwrite: "auto",
                  });
                }
              } else {
                for (let i = visibleCount; i < prevVisible; i += 1) {
                  gsap.to(sortedSquares[i].el, {
                    opacity: 0,
                    duration: 0.6,
                    ease: "power2.out",
                    overwrite: "auto",
                  });
                }
              }
              prevVisible = visibleCount;
            },
          },
          4.0,
        );

        // STAGE 7 (6.6 → 7.2) — MANIFESTO EXITS ALONE, fast and
        // tight. Overlaps the tail of the pixelize so by the time
        // the last pixels finish filling, the manifesto stage has
        // already departed. The amber pixel grid STAYS in place.
        if (stage) {
          tl.to(
            stage,
            { yPercent: -120, opacity: 0, duration: 0.6, ease: "power2.in" },
            6.6,
          );
        }

        // STAGE 8 (7.0 → 8.4) — BRAND ICON SLIDES IN FROM RIGHT,
        // immediately as the pixels finish filling. No dead air —
        // the moment the amber locks, the icon is already on its
        // way in. 1.4s slide gives it weight.
        if (micIcon) {
          tl.to(
            micIcon,
            { xPercent: 0, opacity: 1, duration: 1.4, ease: "power3.out" },
            7.0,
          );
        }

        // STAGE 9 (8.0 → 9.8) — CYAN PATH-LINE MARKER DRAW.
        // Drives stroke-dashoffset 192 → 0 across ALL three lines
        // (core + 2 glow halos) so the halo draws together with
        // the line — no orphan glow visible before/after the core.
        if (micLines.length) {
          tl.to(
            micLines,
            {
              strokeDashoffset: 0,
              duration: 1.8,
              ease: "power1.inOut",
            },
            8.0,
          );
        }

        // STAGE 10 (9.0 → 10.2) — "Go" SLIDES IN FROM RIGHT, lands
        // immediately to the right of the icon to start forming the
        // GoWork lockup.
        if (goRow) {
          tl.to(
            goRow,
            {
              xPercent: 0,
              opacity: 1,
              duration: 1.2,
              ease: "power3.out",
            },
            9.0,
          );
        }

        // STAGE 11 (10.0 → 11.2) — "Work" SLIDES IN FROM RIGHT,
        // joining "Go" to complete the brand lockup "GoWork".
        if (workRow) {
          tl.to(
            workRow,
            {
              xPercent: 0,
              opacity: 1,
              duration: 1.2,
              ease: "power3.out",
            },
            10.0,
          );
        }

        // CHROMATIC ABERRATION — single ramp, no glitch pulse. The
        // user found the morph distracting; instead the offset just
        // settles from a slightly wider entry value (12px) to its
        // resting subtle 3px offset over the wordmark slide-in. The
        // proxy pattern keeps GSAP off the `--abr-x` custom-property
        // which had a silent-fail risk in vars-object form.
        const writeAbr = (v: number) => {
          const s = `${v}px`;
          if (goRow) goRow.style.setProperty("--abr-x", s);
          if (workRow) workRow.style.setProperty("--abr-x", s);
        };
        tl.to(
          abrProxy,
          {
            v: 3,
            duration: 1.6,
            ease: "power3.out",
            onUpdate: () => writeAbr(abrProxy.v),
          },
          9.0,
        );

        // LOCKUP CYAN PATH-LINE — scroll-tied draw across the FULL
        // GoWork lockup (spans Go + Work), starting AFTER both
        // rows have landed. Uses a captured local ref (`lockupRef`)
        // so the onUpdate closure has a non-null HTMLElement type —
        // sidesteps the TS strict-null narrowing that was causing
        // the whole timeline to fall into the catch path.
        if (lockupEl) {
          const lockupRef = lockupEl;
          tl.to(
            lockupLineProxy,
            {
              v: 1,
              duration: 1.4,
              ease: "power2.inOut",
              onUpdate: () =>
                lockupRef.style.setProperty(
                  "--lockup-line-scale",
                  String(lockupLineProxy.v),
                ),
            },
            10.6,
          );
        }

        // STAGE 12 (11.4 → 12.6) — CTA SLIDES IN FROM RIGHT below
        // the GoWork lockup. The mic-drop composition is now
        // complete: brand row on top, CTA underneath.
        if (cta) {
          tl.to(
            cta,
            {
              xPercent: 0,
              opacity: 1,
              duration: 1.2,
              ease: "power3.out",
            },
            11.4,
          );
        }
        if (meta) {
          tl.to(
            meta,
            { opacity: 1, duration: 0.8, ease: "power3.out" },
            11.8,
          );
        }

        // STAGE 13 (12.6 → 13.4) — soft lift on the entire
        // composition (yPercent 0 → -4) for a gentle "settled"
        // breath at the very end. No bounce — the user found the
        // glitch distracting, so the closer reads as calm not jumpy.
        if (wordmark) {
          tl.to(
            wordmark,
            { yPercent: -4, duration: 0.8, ease: "power2.out" },
            12.6,
          );
        }
        if (wordmark) {
          tl.to(
            wordmark,
            { yPercent: 0, duration: 0.8, ease: "power2.inOut" },
            13.4,
          );
        }

        stInst = tl.scrollTrigger ?? null;
      } catch {
        /* GSAP unavailable — fallback: snap to final state */
        el.querySelectorAll<HTMLElement>("[data-ch08-line]").forEach((line) => {
          line.style.transform = "translateX(0)";
          line.style.opacity = "1";
        });
        el.querySelectorAll<HTMLElement>("[data-ch08-row]").forEach((row) => {
          row.style.transform = "translateX(0)";
          row.style.opacity = "1";
          row.style.setProperty("--abr-x", "0px");
        });
        const iconEl = el.querySelector<HTMLElement>("[data-ch08-mic-icon]");
        if (iconEl) {
          iconEl.style.transform = "translateX(0)";
          iconEl.style.opacity = "1";
        }
        el.querySelectorAll<SVGElement>("[data-ch08-mic-line]").forEach(
          (line) => {
            (line as unknown as { style: CSSStyleDeclaration }).style.strokeDashoffset = "0";
          },
        );
        const ctaFallback = el.querySelector<HTMLElement>("[data-ch08-cta]");
        if (ctaFallback) {
          ctaFallback.style.transform = "translateX(0)";
          ctaFallback.style.opacity = "1";
        }
        const metaFallback = el.querySelector<HTMLElement>("[data-ch08-meta]");
        if (metaFallback) metaFallback.style.opacity = "1";
        const lockupCatchEl = el.querySelector<HTMLElement>(
          "[data-ch08-mic-lockup]",
        );
        if (lockupCatchEl)
          lockupCatchEl.style.setProperty("--lockup-line-scale", "1");
        el.querySelectorAll<HTMLElement>(".ch08-square").forEach((sq) => {
          (sq as HTMLElement).style.opacity = "0";
        });
      }
    })();

    return () => {
      cancelled = true;
      try {
        stInst?.kill?.();
      } catch {
        /* ignore */
      }
    };
  }, [reduced]);

  const onCtaClick = (e: MouseEvent<HTMLAnchorElement>) => {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
    if (!vtSupported || reduced) return;
    e.preventDefault();
    const doc = document as unknown as {
      startViewTransition?: (cb: () => void) => unknown;
    };
    if (typeof doc.startViewTransition !== "function") {
      router.push("/assess");
      return;
    }
    doc.startViewTransition(() => {
      router.push("/assess");
    });
  };

  const line4Raw = t("home.ch8.line4");
  const tuesday = t("home.ch8.line4Tuesday");
  const [l4a, l4b] = line4Raw.split("{{tuesday}}");

  const onWordmarkEnter = () => {
    setHovered(true);
    setCityIdx((i) => (i + 1) % SPOKEN_CITIES.length);
  };
  const onWordmarkLeave = () => setHovered(false);

  // Brand mark text — mixed case to match the official brand mark
  // (`brand-mark.html` → "GoWork"). Hardcoded since the wordmark is
  // a brand asset, not a translatable string. The "GO"/"WORK"
  // upper-case i18n keys are still used as accessible labels for
  // localized screen readers via aria-label below.
  const row1 = "Go";
  const row2 = "Work";
  const spokenCity = t("home.ch8.wordmark.spokenCityFw");
  const comingPrefix = t("home.ch8.wordmark.spokenCityComing");

  return (
    <section
      ref={sectionRef}
      id={id}
      data-bg="warm"
      data-screen-label="08 Find your path"
      data-motion={reduced ? "off" : "on"}
      aria-labelledby="ch08-h2"
      className="chapter ch08"
      style={{
        position: "relative",
        background:
          "linear-gradient(180deg, rgba(245,158,11,0.06), rgba(245,158,11,0.02) 60%, transparent), var(--bg-base)",
        overflow: "hidden",
        minHeight: "100vh",
      }}
    >
      {/* Ambient ground layers — moved to z-index 4 (same level as
       *  the amber pixel grid) and rendered AFTER it in DOM order
       *  so they overlay the locked-amber field instead of sitting
       *  behind it. mix-blend-mode: screen brightens the amber to
       *  produce gradient variation (mesh) and a slow continuous
       *  light sweep across the GoWork composition. The mic-drop
       *  (z-index 5) still sits on top of everything. */}
      <div
        className="ch08-stage"
        data-ch08-stage
        style={{
          // Stage absolute-positioned on the section so it occupies the
          // full pin viewport. GSAP slides this entire container up and
          // out at stage 7 of the timeline; the wordmark behind it
          // (z-index: 0) becomes the closing image.
          position: "absolute",
          inset: 0,
          padding: "120px 80px 120px",
          display: "grid",
          gridTemplateRows: "auto 1fr auto",
          gap: "32px",
          maxWidth: "min(1400px, 100%)",
          margin: "0 auto",
          zIndex: 2,
          willChange: "transform, opacity",
        }}
      >
        <span
          className="ch08-eb"
          data-ch08-eyebrow
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "12px",
            fontFamily: "var(--font-mono-data)",
            fontSize: "11px",
            letterSpacing: "0.16em",
            textTransform: "uppercase",
            color: "var(--fg-muted)",
            willChange: "transform, opacity",
          }}
        >
          <span className="num" style={{ color: "var(--accent-amber)", fontWeight: 600 }}>
            08
          </span>
          <span className="lab">{t("home.ch8.eyebrow")}</span>
        </span>

        <h2
          id="ch08-h2"
          className="ch08-h2"
          style={{
            fontSize: "clamp(2.4rem, 1.4rem + 3.4vw, 6rem)",
            fontWeight: 800,
            letterSpacing: "-0.035em",
            lineHeight: 1.06,
            margin: 0,
          }}
        >
          <span
            data-ch08-line="1"
            className="line"
            style={{ display: "block", willChange: "transform, opacity" }}
          >
            {t("home.ch8.line1")}
          </span>
          <span
            data-ch08-line="2"
            className="line italic-axis"
            style={{
              display: "block",
              fontStyle: "oblique -10deg",
              willChange: "transform, opacity",
            }}
          >
            {t("home.ch8.line2")}
          </span>
          <span
            data-ch08-line="3"
            className="line"
            style={{ display: "block", willChange: "transform, opacity" }}
          >
            {t("home.ch8.line3")}
          </span>
          <span
            data-ch08-line="4"
            className="line"
            style={{ display: "block", willChange: "transform, opacity" }}
          >
            {l4a}
            <em
              style={{
                background:
                  "linear-gradient(90deg, var(--accent-amber), var(--accent-rose))",
                WebkitBackgroundClip: "text",
                backgroundClip: "text",
                color: "transparent",
                fontStyle: "normal",
                fontWeight: 800,
              }}
            >
              {tuesday}
            </em>
            {l4b ?? ""}
          </span>
        </h2>
      </div>

      {/* Amber pixel curtain — z-index 4. Above the manifesto (z=3),
       *  beneath the mic-drop composition (z=5). Squares fade IN
       *  during the pixelize stage and stay locked at full amber
       *  through the rest of the timeline so the section becomes a
       *  brand-amber field that GO WORK lands on top of. */}
      <div
        className="ch08-pixel-grid"
        data-ch08-pixel-grid
        aria-hidden="true"
      />

      {/* Ambient overlay layers REMOVED — the gradient effect now
       *  lives INSIDE the pixel grid itself. Each square's
       *  background colour is mixed from the brand palette (amber
       *  → rose → cyan) based on its (col, row) position, so when
       *  the pixelize stage fills the grid the result IS a brand
       *  gradient — not a flat amber wash with overlay layers
       *  floating in front. Section bg stays clean navy until the
       *  pixels arrive. */}

      {/* GoWork MIC-DROP — z-index 5, on top of the amber curtain.
       *  Vertical layout: [icon][GoWork] inline brand row on top,
       *  CTA cluster below. Mirrors the website chrome brand mark
       *  scaled to hero. Each piece slides in from the RIGHT in
       *  sequence: icon → cyan line draws (marker slow) → Go → Work
       *  joins to form GoWork → CTA arrives below. */}
      <div
        className="ch08-wordmark ch08-mic-drop"
        data-ch08-wordmark
        style={{ color: "var(--fg-primary)" }}
      >
        <div className="ch08-mic-drop__brand">
          <svg
            className="ch08-brand-icon"
            data-ch08-mic-icon
            /* viewBox extended to 18 wide (was 16) so the cyan
             * path-line + its glow halos at x=16 have clearance
             * before the right edge clips. */
            viewBox="0 0 18 16"
            aria-hidden="true"
            fill="none"
            preserveAspectRatio="xMidYMid meet"
            overflow="visible"
          >
            <path
              d="M 14 8 A 6 6 0 1 0 8 14"
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="ch08-brand-icon__arc"
            />
            {/* Cyan path-line + 2 SIBLING GLOW HALOS underneath.
             * Drop-shadow / box-shadow on a thin line paints its
             * bounding rect (boxy halo); duplicate `<line>` strokes
             * at thicker widths + lower opacity paint a TRUE round
             * halo around the line's shape. All three carry the
             * `data-ch08-mic-line` attribute so GSAP animates the
             * stroke-dashoffset on all of them in lockstep — the
             * glow draws WITH the line, not before/after. */}
            <line
              x1={8}
              y1={8}
              x2={16}
              y2={8}
              strokeLinecap="round"
              className="ch08-brand-icon__line ch08-brand-icon__line--halo-wide"
              data-ch08-mic-line
            />
            <line
              x1={8}
              y1={8}
              x2={16}
              y2={8}
              strokeLinecap="round"
              className="ch08-brand-icon__line ch08-brand-icon__line--halo-mid"
              data-ch08-mic-line
            />
            <line
              x1={8}
              y1={8}
              x2={16}
              y2={8}
              strokeLinecap="round"
              className="ch08-brand-icon__line ch08-brand-icon__line--core"
              data-ch08-mic-line
            />
          </svg>
          {/* Lockup span — Go and Work as inline siblings with NO
           *  whitespace between them so they render as the brand
           *  asset "GoWork" once both have slid in. */}
          <span className="ch08-mic-drop__lockup" data-ch08-mic-lockup>
            <span
              className="wm-row wm-row-1 ch08-aberration"
              data-ch08-row="row1"
              data-spoken-city={spokenCity}
              tabIndex={0}
              onPointerEnter={onWordmarkEnter}
              onPointerLeave={onWordmarkLeave}
              onFocus={onWordmarkEnter}
              onBlur={onWordmarkLeave}
              aria-label={
                spokenCity
                  ? `${spokenCity}. ${comingPrefix} ${SPOKEN_CITIES[cityIdx]}.`
                  : undefined
              }
              style={{
                display: "inline-block",
                fontWeight: 900,
                letterSpacing: "-0.05em",
                lineHeight: 0.9,
                fontFeatureSettings: '"ss01"',
                position: "relative",
                pointerEvents: "auto",
                willChange: "transform, opacity",
              }}
            >
              {row1}
              {hovered && spokenCity && comingPrefix ? (
                <span
                  className="ch08-wordmark__tooltip"
                  role="tooltip"
                  style={{
                    position: "absolute",
                    bottom: "-48px",
                    left: 0,
                    padding: "8px 14px",
                    borderRadius: "999px",
                    background: "rgba(10,14,26,0.92)",
                    border:
                      "1px solid color-mix(in oklch, var(--accent-cyan), transparent 60%)",
                    color: "var(--fg-primary)",
                    fontSize: "13px",
                    fontFamily: "var(--font-mono-data)",
                    whiteSpace: "nowrap",
                    pointerEvents: "auto",
                    textShadow: "none",
                    filter: "none",
                  }}
                >
                  GoWork is in {spokenCity}. {comingPrefix} {SPOKEN_CITIES[cityIdx]}.
                </span>
              ) : null}
            </span>
            <span
              className="wm-row wm-row-2 ch08-aberration"
              data-ch08-row="row2"
              style={{
                display: "inline-block",
                fontWeight: 900,
                letterSpacing: "-0.05em",
                lineHeight: 0.9,
                fontFeatureSettings: '"ss01"',
                willChange: "transform, opacity",
              }}
            >
              {row2}
            </span>
          </span>
        </div>

        {/* CTA cluster — sits BELOW the GoWork lockup. Slides in
         *  from the right (matches the brand entry direction) once
         *  the wordmark has landed. */}
        <div
          className="ch08-mic-drop__cta"
          data-ch08-cta
        >
          <a
            className="cta cta-primary cta-xl"
            href="/assess"
            onClick={onCtaClick}
            style={{ viewTransitionName: "ch8-cta-pill" }}
          >
            <span>{t("home.ch8.ctaPrimary")}</span>
            <span className="cta-arr">→</span>
          </a>
          <span className="ch08-meta" data-ch08-meta>
            {t("home.ch8.ctaMeta")}
          </span>
        </div>
      </div>
    </section>
  );
}

