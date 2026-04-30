"use client";

/**
 * HomePage — sprint/gowork-facelift Driver D (Phase D3) /
 * sprint/polish-2 Driver E (T48–T59 wiring).
 *
 * Top-level shell for the 8-chapter scrollytelling homepage. Mounts the
 * dedicated chrome (SiteHeader / ChapterRail / PageMeta / SiteFooter +
 * CursorFlashlight) and lazy-loads each chapter so GSAP / ScrollTrigger
 * / Lenis only register on the client side.
 *
 * polish-2 additions (Driver E):
 *   - TitleSequenceGate (T49)         — first-paint title bumper
 *   - Ch01CursorTrail   (T48)         — Ch1-only amber particle wake
 *   - ScrollVelocityBridge (T56/57/59) — body-attr writer for spotlights
 *   - EyebrowActiveBridge (T55)       — variable-font axis on active ch
 *   - FpsOverlayGate    (T54)         — dev-only FPS HUD
 *   - sound-trigger listener (T50)    — chapters fire DOM events; we play
 */
import dynamic from "next/dynamic";
import { ChapterRail } from "@/components/home/ChapterRail";
import { CursorFlashlight } from "@/components/home/CursorFlashlight";
import { PageMeta } from "@/components/home/PageMeta";
import { SiteFooter } from "@/components/home/SiteFooter";
import { SiteHeader } from "@/components/home/SiteHeader";
import { Ch01CursorTrail } from "@/components/home/Ch01CursorTrail";
import { TitleSequenceGate } from "@/components/home/TitleSequenceGate";
import { ScrollVelocityBridge } from "@/components/home/ScrollVelocityBridge";
import { EyebrowActiveBridge } from "@/components/home/EyebrowActiveBridge";
import { FpsOverlayGate } from "@/components/home/FpsOverlayGate";
import { useEffect, useState } from "react";
import { useScrollProgress } from "@/hooks/useScrollProgress";
import { useActiveSection } from "@/hooks/useActiveSection";
import { installSoundTriggers } from "@/lib/home/soundTriggers";

// Section anchors in narrative order — leading-zero ids match the
// chapter sections rendered in the JSX below.
const CHAPTER_SECTION_IDS = [
  "chapter-01",
  "chapter-02",
  "chapter-03",
  "chapter-04",
  "chapter-05",
  "chapter-06",
  "chapter-07",
  "chapter-08",
] as const;

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
  const { totalProgress } = useScrollProgress(TOTAL_CHAPTERS);
  const hour = useCurrentHour();
  // polish-3 fix — replace the bucket-math active chapter (which drifted
  // when sections aren't equal heights, e.g. Ch08 sticky pin = 220vh)
  // with an IntersectionObserver per-section detector. The rail now
  // marks "Ch4 / The map" while the user is reading the map, not Ch5.
  const activeChapter = useActiveSection({
    sectionIds: CHAPTER_SECTION_IDS,
  });

  // Cross-driver sound-trigger listener (T50) — chapters fire DOM events,
  // this hook plays the matching sound.
  useEffect(() => {
    return installSoundTriggers();
  }, []);

  return (
    <>
      <TitleSequenceGate />
      <CursorFlashlight />
      <Ch01CursorTrail />
      <ScrollVelocityBridge />
      <EyebrowActiveBridge />
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
      <FpsOverlayGate chapter={activeChapter} />
    </>
  );
}
