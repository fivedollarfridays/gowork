"use client";

import {
  LazyMotion, domAnimation, m, useReducedMotion,
  useInView, useSpring, useMotionValue, useTransform,
} from "framer-motion";
import { useRef, useEffect, type ReactNode } from "react";

export function MotionProvider({ children }: { children: ReactNode }) {
  return (
    <LazyMotion features={domAnimation} strict>
      {children}
    </LazyMotion>
  );
}

interface ScrollRevealProps {
  children: ReactNode;
  delay?: number;
  className?: string;
  direction?: "up" | "down" | "left" | "right";
}

const directionOffset = { up: [0, 24], down: [0, -24], left: [24, 0], right: [-24, 0] };

export function ScrollReveal({ children, delay = 0, className, direction = "up" }: ScrollRevealProps) {
  const prefersReduced = useReducedMotion();
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-50px" });
  if (prefersReduced) return <div className={className}>{children}</div>;
  const [x, y] = directionOffset[direction];
  return (
    <m.div
      ref={ref}
      className={className}
      initial={{ opacity: 0, x, y }}
      animate={inView ? { opacity: 1, x: 0, y: 0 } : undefined}
      transition={{ duration: 1.0, ease: "easeOut", delay }}
    >
      {children}
    </m.div>
  );
}

interface StaggerContainerProps { children: ReactNode; className?: string; delay?: number }

export function StaggerContainer({ children, className, delay = 0 }: StaggerContainerProps) {
  const prefersReduced = useReducedMotion();
  if (prefersReduced) return <div className={className}>{children}</div>;
  return (
    <m.div
      className={className}
      initial="hidden"
      animate="visible"
      variants={{ visible: { transition: { staggerChildren: 0.25, delayChildren: delay } } }}
    >
      {children}
    </m.div>
  );
}

interface StaggerItemProps { children: ReactNode; className?: string }

export function StaggerItem({ children, className }: StaggerItemProps) {
  const prefersReduced = useReducedMotion();
  const cls = className ? `h-full ${className}` : "h-full";
  if (prefersReduced) return <div className={cls}>{children}</div>;
  return (
    <m.div
      className={cls}
      variants={{
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } },
      }}
    >
      {children}
    </m.div>
  );
}

interface AnimatedCounterProps {
  from?: number; to: number; prefix?: string;
  suffix?: string; duration?: number; decimals?: number;
}

export function AnimatedCounter({
  from = 0, to, prefix = "", suffix = "", duration = 2.5, decimals = 0,
}: AnimatedCounterProps) {
  const prefersReduced = useReducedMotion();
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-50px" });
  const motionValue = useMotionValue(from);
  const spring = useSpring(motionValue, { duration: duration * 1000, bounce: 0.1 });
  const display = useTransform(spring, (v) => `${prefix}${v.toFixed(decimals)}${suffix}`);
  useEffect(() => { if (inView) motionValue.set(to); }, [inView, motionValue, to]);

  if (prefersReduced) {
    return <span>{prefix}{to.toFixed(decimals)}{suffix}</span>;
  }
  return <m.span ref={ref}>{display}</m.span>;
}

interface TypewriterProps { text: string; delay?: number; className?: string }

export function Typewriter({ text, delay = 0, className }: TypewriterProps) {
  const prefersReduced = useReducedMotion();
  if (prefersReduced) return <span className={className}>{text}</span>;
  const words = text.split(" ");
  return (
    <m.span
      className={className}
      initial="hidden"
      animate="show"
      variants={{
        hidden: {},
        show: { transition: { staggerChildren: 0.12, delayChildren: delay } },
      }}
    >
      {words.map((word, i) => (
        <m.span
          key={i}
          style={{ display: "inline-block" }}
          variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } }}
        >
          {word}
          {i < words.length - 1 && "\u00A0"}
        </m.span>
      ))}
    </m.span>
  );
}

interface SlideInProps {
  children: ReactNode; direction?: "left" | "right" | "up" | "down";
  delay?: number; className?: string;
}

export function SlideIn({ children, direction = "left", delay = 0, className }: SlideInProps) {
  const prefersReduced = useReducedMotion();
  if (prefersReduced) return <div className={className}>{children}</div>;
  const [x, y] = directionOffset[direction];
  return (
    <m.div
      className={className}
      initial={{ opacity: 0, x, y }}
      animate={{ opacity: 1, x: 0, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut", delay }}
    >
      {children}
    </m.div>
  );
}

interface ShimmerBarProps { width?: string; height?: string; className?: string }

export function ShimmerBar({ width = "100%", height = "1rem", className }: ShimmerBarProps) {
  const prefersReduced = useReducedMotion();
  if (prefersReduced) {
    return <div className={`rounded bg-muted ${className ?? ""}`} style={{ width, height }} />;
  }
  return (
    <div className={`relative rounded bg-muted/80 overflow-hidden ${className ?? ""}`} style={{ width, height }}>
      <m.div
        className="absolute inset-0"
        style={{
          background: "linear-gradient(90deg, transparent 25%, rgba(255,255,255,0.25) 50%, transparent 75%)",
          backgroundSize: "200% 100%",
        }}
        animate={{ backgroundPosition: ["-200% 0", "200% 0"] }}
        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
      />
    </div>
  );
}
