"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef, type ReactNode } from "react";
import { useReducedMotion } from "framer-motion";

interface ViewTransitionsProviderProps {
  children: ReactNode;
}

export function ViewTransitionsProvider({ children }: ViewTransitionsProviderProps) {
  const pathname = usePathname();
  const prevPathname = useRef(pathname);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    if (pathname !== prevPathname.current) {
      prevPathname.current = pathname;
      if (
        !reducedMotion &&
        typeof document !== "undefined" &&
        "startViewTransition" in document
      ) {
        (document as unknown as { startViewTransition: (cb: () => void) => void })
          .startViewTransition(() => {});
      }
    }
  }, [pathname, reducedMotion]);

  return <>{children}</>;
}
