"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef, type ReactNode } from "react";

interface ViewTransitionsProviderProps {
  children: ReactNode;
}

export function ViewTransitionsProvider({ children }: ViewTransitionsProviderProps) {
  const pathname = usePathname();
  const prevPathname = useRef(pathname);

  useEffect(() => {
    if (pathname !== prevPathname.current) {
      prevPathname.current = pathname;
      if (typeof document !== "undefined" && "startViewTransition" in document) {
        (document as unknown as { startViewTransition: () => void }).startViewTransition();
      }
    }
  }, [pathname]);

  return <>{children}</>;
}
