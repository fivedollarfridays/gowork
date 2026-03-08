"use client";

import { m, useScroll, useSpring, useReducedMotion } from "framer-motion";

export function ScrollProgress() {
  const prefersReduced = useReducedMotion();
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001,
  });

  if (prefersReduced) return null;

  return (
    <m.div
      role="progressbar"
      aria-label="Page scroll progress"
      className="fixed top-0 left-0 right-0 h-0.5 bg-secondary z-[60] origin-left"
      style={{ scaleX }}
    />
  );
}
