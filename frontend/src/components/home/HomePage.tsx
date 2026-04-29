"use client";

/**
 * HomePage — sprint/gowork-facelift Driver D (Phase D3).
 *
 * Top-level shell for the 8-chapter scrollytelling homepage. Mounts the
 * dedicated chrome (SiteHeader / ChapterRail / PageMeta / SiteFooter +
 * CursorFlashlight) and lazy-loads each chapter so GSAP / ScrollTrigger
 * / Lenis only register on the client side.
 *
 * Mount order:
 *   1. CursorFlashlight   (fixed, behind everything else)
 *   2. SiteHeader         (sticky, top of page)
 *   3. ChapterRail        (right-edge fixed, xl+ only)
 *   4. PageMeta           (bottom-right fixed, lg+ only)
 *   5. <main>             (chapter content, scroll-driven)
 *   6. SiteFooter         (bottom of document)
 *
 * Each chapter component lives in its own file and imports GSAP at
 * module scope. To keep the SSR pass clean, every chapter is loaded via
 * `next/dynamic({ ssr: false })`. This also keeps the initial bundle
 * small — the chapters that haven't entered the viewport stay deferred.
 *
 * The chapter loaders use the `.then(m => m.ChapterXX)` form because
 * Driver A's Ch1–Ch4 export the chapter as a NAMED export. Ch4 also
 * exports a default; both forms are accepted. Ch5–Ch8 follow the same
 * named-export contract.
 *
 * State: ChapterRail and PageMeta are stateless; this shell drives them
 * with `useScrollProgress(8)` and `useTimeOfDay()` so the bottom-right
 * HUD reflects the actual page state.
 */
import dynamic from "next/dynamic";
import { ChapterRail } from "@/components/home/ChapterRail";
import { CursorFlashlight } from "@/components/home/CursorFlashlight";
import { PageMeta } from "@/components/home/PageMeta";
import { SiteFooter } from "@/components/home/SiteFooter";
import { SiteHeader } from "@/components/home/SiteHeader";
import { useEffect, useState } from "react";
import { useScrollProgress } from "@/hooks/useScrollProgress";

const TOTAL_CHAPTERS = 8;
const HOME_CITY = "Fort Worth, TX";

/**
 * Returns the current local hour (0..23). SSR-safe: starts at 12 (noon)
 * and updates after the first client effect tick. Re-runs every minute.
 */
function useCurrentHour(): number {
  const [hour, setHour] = useState<number>(12);
  useEffect(() => {
    const tick = () => setHour(new Date().getHours());
    tick();
    const id = window.setInterval(tick, 60_000);
    return () => window.clearInterval(id);
  }, []);
  return hour;
}

const Chapter01TheWall = dynamic(
  () =>
    import("@/components/home/chapters/Chapter01TheWall").then(
      (m) => m.Chapter01TheWall,
    ),
  { ssr: false },
);
const Chapter02TheNumbers = dynamic(
  () =>
    import("@/components/home/chapters/Chapter02TheNumbers").then(
      (m) => m.Chapter02TheNumbers,
    ),
  { ssr: false },
);
const Chapter03MeetCarlos = dynamic(
  () =>
    import("@/components/home/chapters/Chapter03MeetCarlos").then(
      (m) => m.Chapter03MeetCarlos,
    ),
  { ssr: false },
);
const Chapter04TheMap = dynamic(
  () =>
    import("@/components/home/chapters/Chapter04TheMap").then(
      (m) => m.Chapter04TheMap ?? m.default,
    ),
  { ssr: false },
);
const Chapter05ThePlan = dynamic(
  () =>
    import("@/components/home/chapters/Chapter05ThePlan").then(
      (m) => m.Chapter05ThePlan,
    ),
  { ssr: false },
);
const Chapter06LiveJobs = dynamic(
  () =>
    import("@/components/home/chapters/Chapter06LiveJobs").then(
      (m) => m.Chapter06LiveJobs,
    ),
  { ssr: false },
);
const Chapter07TheCliff = dynamic(
  () =>
    import("@/components/home/chapters/Chapter07TheCliff").then(
      (m) => m.Chapter07TheCliff,
    ),
  { ssr: false },
);
const Chapter08FindYourPath = dynamic(
  () =>
    import("@/components/home/chapters/Chapter08FindYourPath").then(
      (m) => m.Chapter08FindYourPath,
    ),
  { ssr: false },
);

export default function HomePage(): JSX.Element {
  const { chapter, totalProgress } = useScrollProgress(TOTAL_CHAPTERS);
  const hour = useCurrentHour();
  const activeChapter = Math.min(TOTAL_CHAPTERS, Math.max(1, chapter + 1));

  return (
    <>
      <CursorFlashlight />
      <SiteHeader />
      <ChapterRail activeChapter={activeChapter} progress={totalProgress} />
      <PageMeta
        city={HOME_CITY}
        chapter={activeChapter}
        totalChapters={TOTAL_CHAPTERS}
        progress={totalProgress}
        hour={hour}
      />
      <main id="home-main" data-home-main="true">
        <Chapter01TheWall />
        <Chapter02TheNumbers />
        <Chapter03MeetCarlos />
        <Chapter04TheMap />
        <Chapter05ThePlan />
        <Chapter06LiveJobs />
        <Chapter07TheCliff />
        <Chapter08FindYourPath />
      </main>
      <SiteFooter />
    </>
  );
}
