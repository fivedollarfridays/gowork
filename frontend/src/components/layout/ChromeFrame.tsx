"use client";

/**
 * ChromeFrame — sprint/gowork-facelift Driver D (Phase D3).
 *
 * Wrapper for the canonical app-chrome (Header + Footer) that renders
 * children on every route EXCEPT `/`. The home route mounts the
 * facelift's dedicated `<SiteHeader>` + `<SiteFooter>` (Driver A's
 * scrollytelling chrome), so the canonical app chrome must not double up.
 *
 * SSR-safe: if `usePathname()` returns null (initial render before the
 * router is ready), this falls through to rendering children — i.e. the
 * canonical chrome shows. The canonical chrome is the safer default
 * because every non-home route is supposed to have it.
 */
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const HOME_ROUTE = "/";

export interface ChromeFrameProps {
  children: ReactNode;
}

export function ChromeFrame({ children }: ChromeFrameProps): JSX.Element | null {
  const pathname = usePathname();
  if (pathname === HOME_ROUTE) {
    return null;
  }
  return <>{children}</>;
}
