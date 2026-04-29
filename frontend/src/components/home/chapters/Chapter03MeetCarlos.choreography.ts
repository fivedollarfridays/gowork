/**
 * Chapter 03 GSAP scroll-trigger choreography.
 *
 * Pulled out of `Chapter03MeetCarlos.tsx` to keep that component lean and
 * under arch limits. Owns:
 *
 *   - portrait entry slide-in
 *   - h2 word stagger
 *   - paragraph + facts entry stagger
 *   - portrait scroll parallax (y -60)
 *   - T16: per-z-layer parallax (data-parallax-velocity drives translateY)
 *   - T18: count-up tween for each `.fact[data-countup]` numeric chip
 *
 * Reduced-motion: the caller hooks `useGsapScrollTrigger` checks `reduced`
 * before invoking us; we treat the call as motion-on by contract.
 */

interface GsapLike {
  from: (target: unknown, vars: Record<string, unknown>) => unknown;
  to: (target: unknown, vars: Record<string, unknown>) => unknown;
}

/**
 * T18 — render an in-flight count-up value while preserving the original
 * fact text suffix (e.g., "2:30" → "0:30"...→ "2:30"). For numbers without
 * a colon we just round.
 */
function renderCountUp(value: number, finalText: string): string {
  const colonIdx = finalText.indexOf(":");
  if (colonIdx > 0) {
    const tail = finalText.slice(colonIdx);
    return `${Math.round(value)}${tail}`;
  }
  return Math.round(value).toString();
}

function entranceStagger(el: HTMLElement, gsap: GsapLike): void {
  gsap.from(el.querySelectorAll(".ch03-portrait"), {
    x: -80,
    opacity: 0,
    duration: 1.2,
    ease: "power3.out",
    scrollTrigger: {
      trigger: el,
      start: "top 60%",
      toggleActions: "play none none reverse",
    },
  });
  gsap.from(el.querySelectorAll(".ch03-h2 .word"), {
    y: 40,
    opacity: 0,
    duration: 0.8,
    stagger: 0.06,
    ease: "power3.out",
    scrollTrigger: {
      trigger: el.querySelector(".ch03-h2"),
      start: "top 70%",
      toggleActions: "play none none reverse",
    },
  });
  gsap.from(el.querySelectorAll(".ch03-p"), {
    y: 24,
    opacity: 0,
    duration: 0.8,
    stagger: 0.15,
    ease: "power3.out",
    scrollTrigger: {
      trigger: el.querySelector(".ch03-p"),
      start: "top 80%",
      toggleActions: "play none none reverse",
    },
  });
  gsap.from(el.querySelectorAll(".ch03-facts .fact"), {
    y: 24,
    opacity: 0,
    duration: 0.6,
    stagger: 0.1,
    ease: "power3.out",
    scrollTrigger: {
      trigger: el.querySelector(".ch03-facts"),
      start: "top 85%",
      toggleActions: "play none none reverse",
    },
  });
}

function portraitParallax(el: HTMLElement, gsap: GsapLike): void {
  gsap.to(el.querySelector(".ch03-portrait"), {
    y: -60,
    scrollTrigger: {
      trigger: el,
      start: "top bottom",
      end: "bottom top",
      scrub: true,
    },
  });
  // T16 — per-z-layer parallax tween. Each <g data-parallax-z> rides
  // a different translateY velocity for depth: 1=-20, 2=-50, 3=-90.
  el.querySelectorAll<SVGGElement>(".ch03-portrait [data-parallax-z]").forEach(
    (g) => {
      const v = parseFloat(g.dataset.parallaxVelocity ?? "0");
      if (!v) return;
      gsap.to(g, {
        y: v,
        scrollTrigger: {
          trigger: el,
          start: "top bottom",
          end: "bottom top",
          scrub: true,
        },
      });
    },
  );
}

function factsCountUp(el: HTMLElement, gsap: GsapLike): void {
  // T18 — count-up tween for each fact's numeric chip.
  el.querySelectorAll<HTMLElement>(".ch03-facts .fact[data-countup]").forEach(
    (fact) => {
      const target = parseFloat(fact.dataset.countup ?? "0");
      if (!Number.isFinite(target) || target <= 0) return;
      const numEl = fact.querySelector<HTMLElement>("[data-stat-num]");
      if (!numEl) return;
      const finalText = numEl.textContent ?? "";
      const obj = { v: 0 };
      gsap.to(obj, {
        v: target,
        duration: 1.4,
        ease: "power2.out",
        scrollTrigger: {
          trigger: fact,
          start: "top 85%",
          toggleActions: "play none none reverse",
        },
        onUpdate: () => {
          numEl.textContent = renderCountUp(obj.v, finalText);
        },
        onComplete: () => {
          numEl.textContent = finalText;
        },
      });
    },
  );
}

/** Top-level entrypoint — wires every Ch03 GSAP timeline. */
export function runCh03Choreography(el: HTMLElement, gsap: GsapLike): void {
  entranceStagger(el, gsap);
  portraitParallax(el, gsap);
  factsCountUp(el, gsap);
}
